from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum

from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()


class Similarity(AbstractAPITaskOnDataset("similarity")):
    algorithm = models.CharField(
        max_length=20,
    )

    def get_task_kwargs(self) -> Dict[str, Any]:
        """Returns kwargs for the API task"""
        kwargs = super().get_task_kwargs()
        kwargs.update(self.parameters)

        # TODO make it return API request parameters
        # params = {
        #     "feat_net": self.cleaned_data['feat_net'],
        #     "feat_set": self.cleaned_data['feat_set'],
        #     "feat_layer": self.cleaned_data['feat_layer']
        #
        # }
        return kwargs
