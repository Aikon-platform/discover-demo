from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
import uuid
import requests
import traceback
from PIL import Image, ImageOps
import zipfile
import json

from datasets.utils import PathAndRename
from tasking.models import AbstractAPITask

User = get_user_model()

path_query_images = PathAndRename("watermarks/queries/")

WATERMARKS_API_URL = getattr(settings, "API_URL", "http://localhost:5000")


class WatermarkProcessing(AbstractAPITask("watermarks")):
    notify_email = False

    # The clustering tracking id
    api_tracking_id = models.UUIDField(null=True, editable=False)

    # Parameters
    image = models.ImageField(upload_to=path_query_images, max_length=300)
    detect = models.BooleanField(
        "Detect and crop watermarks in the image", blank=True, default=True
    )
    compare_to = models.ForeignKey(
        "WatermarksSource", null=True, on_delete=models.SET_NULL, related_name="queries"
    )

    # Results
    annotations = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.image.name

    class Meta:
        ordering = ["-requested_on"]

    def get_absolute_url(self):
        return reverse("watermarks:status", args=[str(self.id)])

    def on_task_success(self, data):
        if data is not None:
            self.annotations = data.get("output", {})
            if self.detect:
                self.crop_boxes()

        self.compress_image()

        return super().on_task_success(data)

    def on_task_error(self, error):
        self.compress_image()
        return super().on_task_error(error)

    def get_task_files(self):
        return {"image": open(self.image.path, "rb")}

    def get_task_kwargs(self):
        return {
            "detect": self.detect,
            "compare_to": self.compare_to.uid if self.compare_to else None,
        }

    def get_bounding_boxes(self, min_score=0.5):
        """
        Return the bounding boxes from the annotations
        """
        if self.annotations is None:
            return []
        detections = self.annotations.get("detection", {})
        bboxes = detections.get("boxes", [])
        scores = detections.get("scores", [])
        return [
            (box, score) for (box, score) in zip(bboxes, scores) if score >= min_score
        ]

    def get_bounding_boxes_as_xywh_pct(self):
        # convert xyxy to xywh and filter out low scores
        return [
            {
                "x": box[0] * 100,
                "y": box[1] * 100,
                "width": (box[2] - box[0]) * 100,
                "height": (box[3] - box[1]) * 100,
                "score": score,
            }
            for (box, score) in self.get_bounding_boxes()
        ]

    def get_crops_urls(self, k=None):
        if k is None:
            k = len(self.get_bounding_boxes())
        image_base_url = self.image.url.rsplit(".", 1)[0]
        return [f"{image_base_url}+{i}.jpg" for i in range(k)]

    def crop_boxes(self):
        """
        Return the cropped image from the annotations
        """
        boxes = self.get_bounding_boxes()
        if not boxes:
            return []
        image = Image.open(self.image)
        image_base_path = self.image.path.rsplit(".", 1)[0]
        crops = []
        for k, (box, score) in enumerate(boxes):
            box = [
                box[0] * image.width,
                box[1] * image.height,
                box[2] * image.width,
                box[3] * image.height,
            ]
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            sz = max(box[2] - box[0], box[3] - box[1]) * 1.20
            x0, y0, x1, y1 = (
                int(cx - sz / 2),
                int(cy - sz / 2),
                int(cx + sz / 2),
                int(cy + sz / 2),
            )
            crop = image.crop((x0, y0, x1, y1))
            crop.thumbnail((512, 512))
            crop.save(f"{image_base_path}+{k}.jpg", quality=85)

    def compress_image(self):
        """
        Compress the image to a smaller size
        """

        img = Image.open(self.image)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((1000, 1000))
        img.save(self.image.path, quality=60)


class WatermarksSource(models.Model):
    uid = models.CharField("UID", max_length=50, unique=True)
    name = models.CharField(max_length=64)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    downloaded = models.BooleanField(default=False)
    size = models.PositiveIntegerField()

    def __str__(self):
        return "Watermark source: " + self.name

    @property
    def data_folder(self):
        return "watermarks/sources/" + self.uid

    @property
    def data_folder_path(self):
        return settings.MEDIA_ROOT / self.data_folder

    @property
    def data_folder_url(self):
        return settings.MEDIA_URL + self.data_folder

    @property
    def index_url(self):
        return self.data_folder_url + "/index.json"

    def download_images(self):
        """
        Download the images from the API
        """
        response = requests.get(
            f"{WATERMARKS_API_URL}/watermarks/sources/{self.uid}/images.zip"
        )
        response.raise_for_status()

        zip_file = self.data_folder_path / "images.zip"
        zip_file.parent.mkdir(parents=True, exist_ok=True)
        with open(zip_file, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(self.data_folder_path)
        zip_file.unlink()

        response = requests.get(
            f"{WATERMARKS_API_URL}/watermarks/sources/{self.uid}/index.json"
        )
        response.raise_for_status()
        index = response.json()
        with open(self.data_folder_path / "index.json", "w") as f:
            json.dump(index, f)

        self.downloaded = True
        self.save()

    @classmethod
    def from_api(cls, uid):
        """
        Create a new source from the API
        """
        sources = cls.get_available_sources()
        data = next((s for s in sources if s["uid"] == uid), None)
        if data is None:
            raise ValueError(f"Source with uid {uid} not found")
        data = data["metadata"]
        return cls(
            uid=uid,
            name=data["name"],
            description=data["description"],
            size=data["size"],
        )

    @staticmethod
    def get_available_sources():
        """
        Get the available sources from the API
        """
        response = requests.get(f"{WATERMARKS_API_URL}/watermarks/sources")
        response.raise_for_status()
        return response.json()
