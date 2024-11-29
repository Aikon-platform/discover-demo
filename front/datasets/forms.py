from django import forms
from django.conf import settings

from .fields import (
    ContentRestrictedFileField,
    URLListField,
    MultipleFileInput,
    URLListWidget,
)
from .models import Dataset
from regions.models import Regions

AVAILABLE_FORMATS = [
    ("pdf", "PDF"),
    ("iiif", "IIIF Manifest(s)"),
    ("zip", "ZIP"),
    ("img", "Image(s)"),
]

# TODO add make it dynamic
DATASET_FIELDS = [
    "dataset_name",
    "format",
    "img_files",
    "zip_file",
    "iiif_manifests",
    "pdf_file",
    "crops",
]

ACCEPTED_IMG_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/tiff",
]


class AbstractDatasetForm(forms.ModelForm):
    class Meta:
        abstract = True
        # model = Dataset
        fields = ("dataset_name",)

    dataset_name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )
    format = forms.ChoiceField(
        label="Type",
        choices=[],  # will be set in __init__
    )
    img_files = ContentRestrictedFileField(
        label="Image",
        help_text="Image files containing the dataset to be processed",
        accepted_types=ACCEPTED_IMG_TYPES,
        required=False,
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=MultipleFileInput(
            attrs={"multiple": True, "extra-class": "format-img format-field"}
        ),
    )
    zip_file = ContentRestrictedFileField(
        label="Zipped Dataset",
        help_text="A .zip file containing the dataset to be processed",
        accepted_types=["application/zip"],
        max_size=104857600,
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"extra-class": "format-zip format-field"}
        ),
    )
    iiif_manifests = URLListField(
        label="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        required=False,
        widget=URLListWidget(attrs={"extra-class": "format-iiif format-field"}),
    )
    pdf_file = ContentRestrictedFileField(
        label="PDF",
        help_text="A .pdf file containing the dataset to be processed",
        accepted_types=["pdf", "application/pdf"],
        required=False,
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=forms.ClearableFileInput(
            attrs={"extra-class": "format-pdf format-field"}
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["format"].choices = AVAILABLE_FORMATS

    def save(self, commit=True):
        instance = super().save(commit=False)
        # todo custom save method for different formats

        instance.format = self.cleaned_data.get("format")
        if commit:
            instance.save()

        return instance


class DatasetForm(AbstractDatasetForm):
    class Meta:
        model = Dataset
