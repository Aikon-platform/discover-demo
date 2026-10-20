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
from inspect import getmro as mro

from tasking.models import AbstractTaskOnDataset
from regions.models import Regions
from similarity.models import Similarity
from datasets.models import Dataset

User = get_user_model()


def AbstractPipelineOnDataset(prefix):
    class Pipeline(AbstractTaskOnDataset(prefix)):
        pipeline = None
        task_names: List[str]  # static version

        class Meta:
            abstract = True

        # overridable dynamic version
        def get_task_names(self):
            return self.task_names

        # alias
        @property
        def tasks(self):
            return self.get_task_names()

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
                self.set_fields_on_terminate()
                self.save()

        def next(self):
            self.status = "RUNNING"
            for task in self.tasks:
                if not self.get_task(task):
                    getattr(self, f"start_{task}_task")()
                    return
            self.status = "SUCCESS"
            self.set_fields_on_terminate()
            self.save()

        def start_task(self):
            self.next()

        def cancel_task(self):
            for task in self.tasks:
                t = self.get_task(task)
                if t and not t.is_finished:
                    t.cancel_task()
            self.status = "CANCELLED"
            self.set_fields_on_terminate()
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

    return Pipeline
