from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
import requests
from PIL import Image, ImageOps
import zipfile
import json
import uuid
from typing import List, Optional

from tasking.models import AbstractTaskOnDataset
from regions.models import Regions
from similarity.models import Similarity
from datasets.models import Dataset

User = get_user_model()


class Pipeline(AbstractTaskOnDataset("pipelines")):
    pipeline = None

    # specific to watermark pipelines
    regions_task = models.ForeignKey(
        Regions,
        verbose_name="Use existing regions...",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    similarity_task = models.ForeignKey(
        Similarity,
        verbose_name="Use existing similarity...",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    tasks = ["regions", "similarity"]

    # Generic pipeline methods
    def get_task(self, task_prefix):
        return getattr(self, f"{task_prefix}_task")

    def all_tasks(self) -> List[Optional[AbstractTaskOnDataset]]:
        return [self.get_task(task) for task in self.tasks]

    def on_task_finished(self, task: AbstractTaskOnDataset):
        if task.status == "SUCCESS":
            self.next()
        else:
            self.status = "ERROR"
            self.is_finished = True
            self.save()

    def next(self):
        self.status = "RUNNING"
        for task in self.tasks:
            print("NEXT TASK IN LIST \n", task, self.get_task(task))
            if not self.get_task(task):
                getattr(self, f"start_{task}_task")()
                return
        self.status = "SUCCESS"
        self.is_finished = True
        self.save()

    def start_task(self):
        self.next()

    def cancel_task(self):
        for task in self.tasks:
            t = self.get_task(task)
            if t and not t.is_finished:
                t.cancel_task()
        self.status = "CANCELLED"
        self.is_finished = True
        self.save()

    def get_progress(self):
        for k, t in enumerate(reversed(self.tasks)):
            task = self.get_task(t)
            if task:
                return task.get_progress()
                return f"RUNNING SUBTASK {len(self.tasks) - k} OF {len(self.tasks)} ({t.upper()})\n\n{task.get_progress()}"
        return {}

    @property
    def full_log(self):
        log = ""
        for t in reversed(self.tasks):
            task = self.get_task(t)
            if task:
                log += f"TASK {t.upper()}\n\n{task.full_log}\n\n"
        return log

    # Specific pipeline methods
    def start_regions_task(self):
        self.regions_task = Regions.objects.create(
            dataset=self.dataset,
            requested_by=self.requested_by,
            notify_email=False,
            pipeline=self,
            parameters={
                "model": "fasterrcnn_watermarks.pth",
                "postprocess": "watermarks",
            },
        )
        self.regions_task.save()
        self.save()
        self.regions_task.start_task()

    def start_similarity_task(self):
        self.similarity_task = Similarity.objects.create(
            dataset=self.dataset,
            requested_by=self.requested_by,
            notify_email=False,
            pipeline=self,
            parameters={"feat_net": "resnet18_watermarks", "algorithm": "cosine"},
            crops=self.regions_task,
        )
        self.similarity_task.save()
        self.save()
        self.similarity_task.start_task()
