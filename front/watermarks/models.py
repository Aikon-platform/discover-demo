from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
import uuid
import requests
import traceback
from PIL import Image, ImageOps
import zipfile

from datasets.utils import PathAndRename

User = get_user_model()

path_query_images = PathAndRename("watermarks/queries/")

WATERMARKS_API_URL = getattr(settings, "API_URL", "http://localhost:5000")


class SingleWatermarkDetection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=64,
        default="watermark",
        blank=True,
        verbose_name="Experiment name",
        help_text="Optional name to identify this clustering experiment",
    )
    image = models.ImageField(upload_to=path_query_images, max_length=300)
    annotations = models.JSONField(null=True, blank=True)

    status = models.CharField(max_length=20, default="PENDING", editable=False)

    is_finished = models.BooleanField(default=False, editable=False)
    requested_on = models.DateTimeField(auto_now_add=True, editable=False)
    requested_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, editable=False
    )

    def __str__(self):
        return self.image.name

    class Meta:
        ordering = ["-requested_on"]

    def get_absolute_url(self):
        return reverse("watermarks:detect-result", args=[str(self.id)])

    def fetch_annotations(self):
        """
        Fetch the annotations from the API
        """
        try:
            response = requests.post(
                f"{WATERMARKS_API_URL}/watermarks/detect",
                files={"image": open(self.image.path, "rb")},
            )
            response.raise_for_status()
            self.annotations = response.json()
            if "error" in self.annotations:
                self.status = "ERROR"
            else:
                self.status = "SUCCESS"
        except (ConnectionError, requests.RequestException) as e:
            self.annotations = {
                "error": "Could not connect to the API",
                "traceback": traceback.format_exc(),
            }
            self.status = "ERROR"
        finally:
            self.is_finished = True
            self.save()

    def bounding_boxes(self):
        """
        Return the bounding boxes from the annotations
        """
        bboxes = self.annotations.get("boxes", [])
        scores = self.annotations.get("scores", [])
        # convert xyxy to xywh and filter out low scores
        return [
            {
                "x": box[0] * 100,
                "y": box[1] * 100,
                "width": (box[2] - box[0]) * 100,
                "height": (box[3] - box[1]) * 100,
                "score": score,
            }
            for (box, score) in zip(bboxes, scores)
            if score > 0.5
        ]

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
    
    def download_images(self):
        """
        Download the images from the API
        """
        response = requests.get(f"{WATERMARKS_API_URL}/watermarks/sources/{self.uid}/images")
        response.raise_for_status()
        
        zip_file = self.data_folder_path / "images.zip"
        with open(zip_file, "wb") as f:
            f.write(response.content)
        with zipfile.ZipFile(zip_file, "r") as z:
            z.extractall(self.data_folder_path)
        zip_file.unlink()

        self.downloaded = True
        self.save()

    @staticmethod
    def get_available_sources(self):
        """
        Get the available sources from the API
        """
        response = requests.get(f"{WATERMARKS_API_URL}/watermarks/sources")
        response.raise_for_status()
        return response.json()