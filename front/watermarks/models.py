from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
import uuid
import requests
import traceback
from PIL import Image, ImageOps

from datasets.utils import PathAndRename

User = get_user_model()

path_query_images = PathAndRename("watermarks/queries/")

WATERMARKS_API_URL = getattr(settings, "WATERMARKS_API_URL", "http://localhost:5000/watermarks/")

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
                f"{WATERMARKS_API_URL}detect",
                files={"image": open(self.image.path, "rb")},
            )
            response.raise_for_status()
            self.annotations = response.json()
            self.status = "SUCCESS"
        except (ConnectionError, requests.RequestException) as e:
            self.annotations = {"error": "Could not connect to the API", "traceback": traceback.format_exc()}
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
            {"x": box[0]*100, "y": box[1]*100, 
             "width": (box[2] - box[0])*100, "height": (box[3] - box[1])*100, 
             "score": score} 
            for (box, score) in zip(bboxes, scores) if score > 0.5]
    
    def compress_image(self):
        """
        Compress the image to a smaller size
        """

        img = Image.open(self.image)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((1000, 1000))
        img.save(self.image.path, quality=60)
