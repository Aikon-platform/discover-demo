import json
from typing import List, Dict, Iterable, Any

from django.urls import reverse
from django.db import models
from django.conf import settings
import requests

from shared.utils import zip_on_the_fly, pprint
from tasking.models import AbstractAPITaskOnDataset


class Regions(AbstractAPITaskOnDataset("regions")):
    regions = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Regions Extraction"

    def __str__(self):
        gen_name = self.name
        if not gen_name:
            model = getattr(self, "parameters", {}).get("model", None)
            gen_name = str(model).replace("_", " ").capitalize() if model else "Crops"
        return (
            f"{gen_name} on {self.dataset.name}"
            if self.dataset
            else f"{gen_name} #{self.pk}"
        )

    def save(self, *args, **kwargs):
        # if not self.name:
        #     self.name = self.__str__()

        super().save()

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        self.regions = {}

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": f"Incorrect output data:\n{pprint(data)}"})
                return
            self.regions = output.get("annotations", {})
            for doc_results in output.get("results_url", []):
                doc_uid = doc_results.get("doc_id")
                annotation_url = doc_results.get("result_url")
                try:
                    response = requests.get(annotation_url, stream=True)
                    response.raise_for_status()
                    # self.regions[doc_uid] = response.json()
                    extraction_ref = annotation_url.split("/")[-1]
                    self.regions[extraction_ref] = response.json()
                except Exception as e:
                    # self.on_task_error(
                    #     {
                    #         "error": f"Could not retrieve regions from {annotation_url}:\n{e}"
                    #     }
                    # )
                    # return
                    continue

            try:
                with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
                    json.dump(self.regions, f)
            except Exception as e:
                self.on_task_error(
                    {
                        "error": f"Could not save extracted regions for {self.dataset.id}:\n{e}"
                    }
                )
                return

            if not self.prepare_dataset_from_api(output):
                return

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
            related_name="+",
        )

        def get_task_kwargs(self) -> Dict[str, Any]:
            """Returns kwargs for the API task"""
            kwargs = super().get_task_kwargs()
            if self.crops:
                kwargs["crops"] = self.crops.get_bounding_boxes()
            return kwargs
        
        def prepare_dataset_from_api(self, output: dict) -> bool:
            """
            Handle the connection between the dataset served by the API and the front-end dataset
            Also crops the images if needed
            """
            
            if not super().prepare_dataset_from_api(output):
                return False

            try:
                if self.crops:
                    self.dataset.apply_cropping(self.crops.get_bounding_boxes())
            except Exception as e:
                self.on_task_error(
                    {"error": f"Could not crop images from {self.crops}:\n{e}"}
                )
                return False
            return True

    return AbstractAPITaskOnCrops
