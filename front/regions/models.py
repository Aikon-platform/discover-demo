import json
from pathlib import Path
import zipfile
from PIL import Image
import traceback
from typing import List, Dict, Iterable

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

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return

            self.regions = output.get("annotations", {})
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

    def get_download_url(self):
        """Get the URL for downloading crops"""
        if self.has_crops:
            return reverse("regions:download", kwargs={"pk": self.pk})
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
        doc_image_map = self.dataset.get_doc_image_mapping()
        for image in self.get_bounding_boxes():
            image = image.get(0, image)  # Old format : single-item lists
            img_name, crops = image.get("source", ""), image.get("crops", [])
            doc_uid = image.get("doc_uid", None)

            print(doc_uid, img_name)
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

    @classmethod
    def get_available_models(cls):
        try:
            response = requests.get(f"{cls.api_endpoint_prefix}/models")
            response.raise_for_status()
            models = response.json()
        except Exception as e:
            print(e)
            return [("", "Unable to fetch available models")]
        if not models:
            return [("", "No available models for extraction")]

        # models = {model: "date", ...}
        return [
            (model, f"{model} (last update: {date})") for model, date in models.items()
        ]
