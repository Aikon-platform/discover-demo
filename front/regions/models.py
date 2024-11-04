import json

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

        # TODO unify and remove usage of zipped_dataset
        self.result_full_path.mkdir(parents=True, exist_ok=True)
        with open(self.result_full_path / f"{self.dataset.id}.json", "w") as f:
            json.dump(data, f, indent=2)

        self.save()

        # TODO turn json files with regions into cropped images
        # TODO trace regions on original images
        # TODO make these actions a task
        # TODO allow images to be downloaded
        return super().on_task_success(data)

    def get_task_kwargs(self):
        dataset = {
            str(self.dataset.id): f"{settings.BASE_URL}{self.dataset.zip_file.url}"
        }
        return {
            "documents": json.dumps(dataset),
            "model": self.model,
            "parameters": json.dumps(self.parameters),
        }
