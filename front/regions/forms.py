import requests
from django import forms
from django.conf import settings

from .models import Regions
from datasets.fields import ContentRestrictedFileField

REGIONS_API_URL = f"{getattr(settings, 'API_URL', 'http://localhost:5001')}/regions"


class RegionsForm(forms.ModelForm):
    class Meta:
        model = Regions
        fields = ("name", "dataset_zip", "dataset_name", "model", "notify_email")

    dataset_zip = ContentRestrictedFileField(
        label="Dataset",
        help_text="A .zip file containing the images to be processed",
        accepted_types=["application/zip"],
        max_size=settings.MAX_UPLOAD_SIZE,
    )
    # dataset_iiif = forms.URLField(
    #     label="IIIF Manifest URL",
    #     help_text="The URL to the IIIF manifest of the dataset",
    #     max_length=500,
    #     required=False,
    # )
    dataset_name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )
    model = forms.ChoiceField(
        label="Model",
        help_text="Model used to extract image regions in the dataset",
        choices=[],  # dynamically set in __init__
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        self.__user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = self.get_available_models()
        self.initial["model"] = None

    def get_available_models(self):
        response = requests.get(f"{REGIONS_API_URL}/models")
        response.raise_for_status()
        models = response.json()
        if not models:
            return [("", "No available models for extraction")]

        # models = {model: "date", ...}
        return [
            (model, f"{model} (last update: {date})") for model, date in models.items()
        ]
