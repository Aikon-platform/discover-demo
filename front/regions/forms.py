import requests
from django import forms
from django.conf import settings

from .models import Regions
from tasking.forms import AbstractTaskOnDatasetForm

REGIONS_API_URL = f"{getattr(settings, 'API_URL', 'http://localhost:5001')}/regions"


class RegionsForm(AbstractTaskOnDatasetForm):
    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Regions
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("model",)

    model = forms.ChoiceField(
        label="Model",
        help_text="Model used to extract image regions in the dataset",
        choices=[],  # dynamically set in __init__
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = self.get_available_models()

    @staticmethod
    def get_available_models():
        try:
            response = requests.get(f"{REGIONS_API_URL}/models")
            response.raise_for_status()
            models = response.json()
        except Exception as e:
            print(e)
            return [("", "Unable to fetch available models")]
        if not models:
            return [("", "No available models for extraction")]

        # models = {model: "date", ...}
        return [
            (model, f"{model} (last update: {date})") for model, date in models.items()
        ]
