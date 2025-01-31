import json
from typing import List, Dict, Iterable, Any

from django.urls import reverse
from django.db import models
from django.conf import settings
import requests

from shared.utils import zip_on_the_fly
from tasking.models import AbstractAPITaskOnDataset


class Regions(AbstractAPITaskOnDataset("regions")):
    # Results
    regions = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Regions Extraction"

    def __str__(self):
        return (
            f"Crops from {self.dataset.name}"
            if self.dataset
            else f"Regions Extraction #{self.pk}"
        )

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        self.regions = {}

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return
            # self.regions = output.get("annotations", {})
            # with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
            #     json.dump(self.regions, f)

            for doc_annotations in output.get("annotations", []):
                # digit_annotations is supposed to be {doc.uid: result_url}
                doc_uid, annotation_url = next(iter(doc_annotations.items()))
                try:
                    response = requests.get(annotation_url, stream=True)
                    response.raise_for_status()
                    # self.regions[doc_uid] = response.json()
                    extraction_ref = annotation_url.split("/")[-1]
                    self.regions[extraction_ref] = response.json()
                except Exception:
                    raise ValueError(
                        f"Could not retrieve annotation from {annotation_url}"
                    )

            with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
                json.dump(self.regions, f)

            dataset_url = output.get("dataset_url")
            if dataset_url:
                self.dataset.api_url = dataset_url
                self.dataset.save()

            result = self.dataset.apply_cropping(self.get_bounding_boxes())
            if "error" in result:
                # self.terminate_task(status="ERROR", error=traceback.format_exc())
                self.on_task_error(result)
                return
        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)

    @property
    def has_crops(self):
        return bool(self.regions)

    @property
    def crop_paths(self):
        if not self.has_crops:
            return []
        return self.dataset.get_paths_for_crops(self.get_bounding_boxes())

    def zip_crops(self) -> Iterable[bytes]:
        """Zip the crops"""
        paths = self.crop_paths
        if not paths:
            return None
        return zip_on_the_fly(
            [(str(p.relative_to(self.dataset.crops_path)), p) for p in paths]
        )

    def get_download_zip_url(self):
        """Get the URL for downloading cropped images in a zip"""
        if self.has_crops:
            return reverse("regions:download_zip", kwargs={"pk": self.pk})
        return None

    def get_download_json_url(self):
        """Get the URL for downloading crops in a json format"""
        if self.has_crops:
            return reverse("regions:download_json", kwargs={"pk": self.pk})
        return None

    def get_bounding_boxes(self) -> List[Dict]:
        """
        Returns a list of {source, doc_id, crops: List[Dict]} dictionaries
        """
        if self.regions is None:
            return []
        return sum(self.regions.values(), [])

    def get_bounding_boxes_for_display(self):
        bbox = []
        dataset = self.dataset
        if not dataset:
            return bbox
        doc_image_map = dataset.get_doc_image_mapping()
        for image in self.get_bounding_boxes():
            image = image.get(0, image)  # Old format : single-item lists
            img_name, crops = image.get("source", ""), image.get("crops", [])
            doc_uid = image.get("doc_uid", None)

            source_img = doc_image_map.get(doc_uid, {}).get(img_name, None)
            source_url = source_img.url if source_img else ""

            formatted_crops = []
            for idx, crop in enumerate(crops):
                crop_path = self.dataset.get_path_for_crop(crop, doc_uid=doc_uid, i=idx)
                crop_url = settings.MEDIA_URL + str(
                    crop_path.relative_to(settings.MEDIA_ROOT)
                )
                relative = crop["relative"]
                formatted_crops.append(
                    {
                        "x": relative["x1"] * 100,
                        "y": relative["y1"] * 100,
                        "width": relative["width"] * 100,
                        "height": relative["height"] * 100,
                        "url": crop_url,
                    }
                )

            bbox.append(
                {
                    "image": {
                        "url": source_url,
                        "path": source_img,
                    },
                    "crops": formatted_crops,
                }
            )

        return bbox


def AbstractAPITaskOnCrops(task_prefix: str):
    class AbstractAPITaskOnCrops(AbstractAPITaskOnDataset(task_prefix)):
        """
        Abstract model for tasks on dataset of images that are sent to the API
        """

        class Meta:
            abstract = True

        crops = models.ForeignKey(
            Regions,
            verbose_name="Use crops from...",
            null=True,
            blank=True,
            on_delete=models.SET_NULL,
            related_name="task_crops",
        )

        def get_task_kwargs(self) -> Dict[str, Any]:
            """Returns kwargs for the API task"""
            kwargs = super().get_task_kwargs()
            if self.crops:
                kwargs["crops"] = self.crops.get_bounding_boxes()
            return kwargs

    return AbstractAPITaskOnCrops
