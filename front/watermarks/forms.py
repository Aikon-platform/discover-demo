from typing import Any, Mapping
from django import forms
from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList

from .models import WatermarkProcessing
from datasets.fields import ContentRestrictedFileField


class WatermarkProcessingForm(forms.ModelForm):
    image = ContentRestrictedFileField(
        label="Upload an image",
        help_text="An image to be processed",
        accepted_types=["image/jpeg", "image/png"],
        max_size=1024 * 1024 * 10,
    )

    class Meta:
        model = WatermarkProcessing
        fields = ["image", "detect", "compare_to"]

    def __init__(self, *args, **kwargs) -> None:
        self.__user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

    def save(self, commit: bool = True) -> Model:
        instance = super().save(commit=False)
        instance.requested_by = self.__user
        instance.name = self.cleaned_data["image"].name

        if commit:
            instance.save()

        return instance
