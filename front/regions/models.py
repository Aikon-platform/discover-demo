import json
import shutil
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings

from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()


class Regions(AbstractAPITaskOnDataset("regions")):
    model = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Regions Extraction"

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
            json.dump(data, f, indent=2)

        self.save()
        result = self.process_images(data)
        if "error" in result:
            self.on_task_error(result)
            return

        return super().on_task_success(data)

    def process_images(self, data):
        try:
            task_ref = next(iter(data["output"]))
            image_data = data["output"][task_ref]

            temp_dir = self.result_full_path / "temp"
            temp_dir.mkdir(exist_ok=True)

            try:
                with ZipFile(self.dataset.full_path, "r") as zipped_data:
                    zipped_data.extractall(temp_dir)

                for page in image_data:
                    image_info = page[0]
                    source = image_info["source"]
                    crops = image_info.get("crops", [])

                    if not crops:
                        continue

                    image_paths = list(temp_dir.glob(f"**/{source}"))
                    if not image_paths:
                        return {"error": f"Could not find {source} in extracted files"}

                    image_path = image_paths[0]

                    try:
                        with Image.open(image_path) as img:
                            for idx, crop in enumerate(crops):
                                bbox = crop["absolute"]
                                crop_coords = (
                                    bbox["x1"],
                                    bbox["y1"],
                                    bbox["x2"],
                                    bbox["y2"],
                                )

                                cropped = img.crop(crop_coords)
                                crop_filename = (
                                    f"{Path(source).stem}_crop_{idx + 1}.jpg"
                                )
                                output_path = self.result_full_path / crop_filename
                                cropped.save(output_path, "JPEG")

                    except Exception as e:
                        return {"error": f"Error processing {source}: {e}"}

            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
        except Exception as e:
            return {"error": f"Error during image processing: {e}"}
        return {"success": "Regions processed successfully"}

    def get_task_kwargs(self):
        dataset = {
            str(self.dataset.id): f"{settings.BASE_URL}{self.dataset.zip_file.url}"
        }
        return {
            "documents": json.dumps(dataset),
            "model": self.model,
            "parameters": json.dumps(self.parameters),
        }
