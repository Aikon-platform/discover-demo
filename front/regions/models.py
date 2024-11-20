import json
from pathlib import Path
import zipfile
from PIL import Image
import traceback

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings

from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()


class Regions(AbstractAPITaskOnDataset("regions")):
    model = models.CharField(max_length=500)
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
                json.dump(self.regions, f, indent=2)

            dataset_url = output.get("dataset_url")
            if dataset_url:
                self.dataset.api_url = dataset_url
                self.dataset.save()

            result = self.crop_regions()
            if "error" in result:
                # self.terminate_task(status="ERROR", error=traceback.format_exc())
                self.on_task_error(result)
                return
        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)

    def crop_regions(self):
        try:
            img_path_map = self.dataset.images
        except Exception as e:
            return {
                "error": f"Error extracting images " + traceback.format_exc(limit=2)
            }

        try:
            try:
                for image in self.get_bounding_boxes():
                    image = image.get(0, image)  # Old format : single-item lists
                    img_name, crops = image.get("source", ""), image.get("crops", [])
                    doc_uid = image.get("doc_uid", None)

                    if not crops:
                        continue

                    img_path = img_path_map.get(doc_uid, {}).get(
                        img_name, [None, None]
                    )[0]

                    if img_path is None:
                        return {"error": f"Image {img_name} not found"}

                    try:
                        with Image.open(img_path) as img:
                            for idx, crop in enumerate(crops):
                                bbox = crop["absolute"]
                                cropped = img.crop(
                                    (
                                        bbox["x1"],
                                        bbox["y1"],
                                        bbox["x2"],
                                        bbox["y2"],
                                    )
                                ).convert("RGB")
                                if cropped.size[0] == 0 or cropped.size[1] == 0:
                                    continue
                                crop_filename = (
                                    f"{Path(img_name).stem}_crop_{idx + 1}.jpg"
                                )
                                cropped.save(
                                    self.result_full_path / crop_filename, "JPEG"
                                )

                    except Exception as e:
                        return {
                            "error": f"Error during {img_name} processing: {traceback.format_exc(limit=2)}"
                        }
            except Exception as e:
                return {
                    "error": f"Error during images processing: {traceback.format_exc(limit=2)}"
                }

            # Check if any crops were created
            if not list(self.result_full_path.glob("*_crop_*.jpg")):
                return {"error": "No regions were successfully processed"}

        except Exception as e:
            return {
                "error": f"Error during image processing: {traceback.format_exc(limit=2)}"
            }

        return {"success": "Regions processed successfully"}

    @property
    def crops(self) -> list:
        return list(self.result_full_path.glob("*_crop_*.jpg"))

    @property
    def has_crops(self) -> bool:
        return any(self.result_full_path.glob("*_crop_*.jpg"))

    def zip_crops(self) -> Path:
        zip_path = self.result_full_path / "crops.zip"
        crop_files = self.crops

        if not crop_files:
            return None

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for crop_file in crop_files:
                zipf.write(crop_file, crop_file.name)

        return zip_path

    def get_download_url(self):
        """Get the URL for downloading crops"""
        if self.has_crops:
            return reverse("regions:download", kwargs={"pk": self.pk})
        return None

    def get_bounding_boxes(self):
        if self.regions is None:
            return []
        return sum(self.regions.values(), [])

    def get_bounding_boxes_for_display(self):
        bbox = []
        paths = self.dataset.images
        for image in self.get_bounding_boxes():
            image = image.get(0, image)  # Old format : single-item lists
            img_name, crops = image.get("source", ""), image.get("crops", [])
            doc_uid = image.get("doc_uid", {})

            source_path = Path(paths[doc_uid][img_name][0])
            source_url = settings.MEDIA_URL + str(
                source_path.relative_to(settings.MEDIA_ROOT)
            )

            formatted_crops = []
            for idx, crop in enumerate(crops):
                crop_filename = f"{Path(img_name).stem}_crop_{idx + 1}.jpg"
                crop_url = f"/media/regions/{self.id}/result/{crop_filename}"
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
                        "path": source_path,
                    },
                    "crops": formatted_crops,
                }
            )

        return bbox

    def get_task_kwargs(self):
        return {
            "documents": json.dumps(self.dataset.documents_for_api()),
            "model": self.model,
            "parameters": json.dumps(self.parameters),
        }
