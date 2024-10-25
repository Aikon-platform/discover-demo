from django.contrib.auth import get_user_model
from django.db import models
import uuid

from datasets.models import ZippedDataset
from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()


class Regions(AbstractAPITaskOnDataset("regions")):
    model = models.CharField(max_length=500)

    class Meta:
        verbose_name = "Regions Extraction"

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.save()

        # TODO turn json files with regions into cropped images
        # TODO trace regions on original images
        # TODO make these actions a task

        return super().on_task_success(data)
