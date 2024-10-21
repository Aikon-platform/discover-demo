from django.contrib.auth import get_user_model
from django.db import models
import uuid

from datasets.models import ZippedDataset, IIIFDataset
from tasking.models import AbstractAPITask

User = get_user_model()


class Regions(AbstractAPITask("regions")):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zip_dataset = models.ForeignKey(ZippedDataset, null=True, on_delete=models.SET_NULL)
    # iiif_dataset = models.ForeignKey(IIIFDataset, null=True, on_delete=models.SET_NULL)
    parameters = models.JSONField(null=True)
    model = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Regions Extraction"

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.save()

        # TODO turn txt files with regions into cropped images
        # TODO trace regions on original images
        # TODO make these actions a task

        return super().on_task_success(data)
