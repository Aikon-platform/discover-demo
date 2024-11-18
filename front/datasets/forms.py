from django import forms
from django.conf import settings

from .fields import ContentRestrictedFileField, URLListField
from .models import Dataset


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ("name", "dataset_zip")

    name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )
    format = forms.ChoiceField(
        label="Type",
        choices=[("zip", "ZIP"), ("iiif", "IIIF Manifest"), ("pdf", "PDF")],
    )
    zip_file = ContentRestrictedFileField(
        label="Zipped Dataset",
        help_text="A .zip file containing the dataset to be processed",
        accepted_types=["application/zip"],
        max_size=104857600,
    )
    iiif_manifests = URLListField(
        label="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        required=False,
    )
    pdf_file = ContentRestrictedFileField(
        label="PDF",
        help_text="A .pdf file containing the dataset to be processed",
        accepted_types=["pdf"],
        max_size=settings.MAX_UPLOAD_SIZE,
    )
