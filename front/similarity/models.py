from typing import Dict, Any
import requests

from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model

from tasking.models import AbstractAPITaskOnDataset

User = get_user_model()
SIMILARITY_API_URL = (
    f"{getattr(settings, 'API_URL', 'http://localhost:5001')}/similarity"
)


class Similarity(AbstractAPITaskOnDataset("similarity")):
    algorithm = models.CharField(
        max_length=20,
        default="cosine",
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

    @staticmethod
    def get_available_models():
        try:
            response = requests.get(f"{SIMILARITY_API_URL}/models")
            response.raise_for_status()
            models = response.json()
            if not models:
                return [("", "No models available")]
            # models = { "ref": { "name": "Display Name", "model": "filename", "desc": "Description" }, ... }
            return [
                (info["model"], f"{info['name']} ({info['desc']})")
                for info in models.values()
            ]
        except Exception as e:
            return [("", f"Error fetching models: {e}")]
