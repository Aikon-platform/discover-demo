from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
import requests
from PIL import Image, ImageOps
import zipfile
import json

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

from pipelines.models import AbstractPipelineOnDataset
from tasking.models import AbstractTaskOnDataset
from regions.models import Regions
from similarity.models import Similarity
from datasets.models import Dataset
from search.models import Index, Query, Indexing

WATERMARKS_REGION_NET = "fasterrcnn_watermark_extraction"
WATERMARKS_FEAT_NET = "resnet18_watermarks"
WATERMARKS_FEAT_NET_SKETCHES = "resnet18_watermarks_conv4"

User = get_user_model()


class WatermarksPipeline(AbstractPipelineOnDataset("watermarks")):
    pipeline = None

    analysis_type = models.CharField(
        "Analysis type",
        max_length=10,
        choices=[
            ("similarity", "Compare watermarks inside dataset"),
            ("indexing", "Index this dataset for future queries"),
            ("query", "Search inside an indexed dataset"),
        ],
    )
    need_regions = models.BooleanField(
        "Detect and crop watermarks",
        default=True,
        blank=True,
        help_text="Disable if your images are already cropped",
    )
    query_target_index = models.ForeignKey(
        Index,
        verbose_name="Query target index",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # sub tasks

    regions_task = models.ForeignKey(
        Regions,
        verbose_name="Watermarks detection task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    similarity_task = models.ForeignKey(
        Similarity,
        verbose_name="Watermarks similarity task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    indexing_task = models.ForeignKey(
        Indexing,
        verbose_name="Indexing task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    query_task = models.ForeignKey(
        Query,
        verbose_name="Query task",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    def get_task_names(self):
        if self.need_regions:
            return ["regions", self.analysis_type]
        return [self.analysis_type]

    @property
    def analysis_task(self):
        return getattr(self, f"{self.analysis_type}_task")

    def start_regions_task(self):
        self.regions_task = Regions.objects.create(
            dataset=self.dataset,
            requested_by=self.requested_by,
            notify_email=False,
            watermarks_pipeline=self,
            parameters={
                "model": WATERMARKS_REGION_NET,
                "postprocess": {"squarify": True, "h_margin": 0.05, "v_margin": 0.05},
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
            watermarks_pipeline=self,
            parameters={
                "feat_net": WATERMARKS_FEAT_NET,
                "algorithm": "cosine",
                "transpositions": ["none", "rot90", "rot270", "hflip", "vflip"],
            },
            crops=self.regions_task,
        )
        self.similarity_task.save()
        self.save()
        self.similarity_task.start_task()

    def start_indexing_task(self):
        are_sketches = self.parameters["are_sketches"]

        net = WATERMARKS_FEAT_NET_SKETCHES if are_sketches else WATERMARKS_FEAT_NET

        self.indexing_task = Indexing.objects.create(
            dataset=self.dataset,
            requested_by=self.requested_by,
            notify_email=False,
            watermarks_pipeline=self,
            parameters={
                "feat_net": net,
                "algorithm": "cosine",
                "transpositions": ["none", "hflip"],
                "are_sketches": are_sketches,
            },
            crops=self.regions_task,
        )
        self.indexing_task.save()
        self.save()
        self.indexing_task.start_task()

    def start_query_task(self):
        self.query_task = Query.objects.create(
            dataset=self.dataset,
            requested_by=self.requested_by,
            notify_email=False,
            watermarks_pipeline=self,
            target_index=self.query_target_index,
            parameters={
                "transpositions": ["none", "rot90", "rot180", "rot270"],
            },
            crops=self.regions_task,
        )
        self.query_task.save()
        self.save()
        self.query_task.start_task()
