from django import forms
from django.conf import settings

from .fields import ContentRestrictedFileField, URLListField
from .models import Dataset

AVAILABLE_FORMATS = [
    ("pdf", "PDF"),
    ("iiif", "IIIF Manifest(s)"),
    ("zip", "ZIP"),
    ("img", "Image(s)"),
]


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ("name",)

    name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )
    format = forms.ChoiceField(
        label="Type",
        choices=AVAILABLE_FORMATS,
    )

    img_files = ContentRestrictedFileField(
        label="Image",
        help_text="Image files containing the dataset to be processed",
        accepted_types=["image"],
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=forms.ClearableFileInput(
            attrs={"multiple": True, "classes": "format-img"}
        ),
    )
    zip_file = ContentRestrictedFileField(
        label="Zipped Dataset",
        help_text="A .zip file containing the dataset to be processed",
        accepted_types=["application/zip"],
        max_size=104857600,
        widget=forms.ClearableFileInput(attrs={"classes": "format-zip"}),
    )
    iiif_manifests = URLListField(
        label="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        required=False,
        widget=forms.CharField(attrs={"classes": "format-iiif"}),
    )
    pdf_file = ContentRestrictedFileField(
        label="PDF",
        help_text="A .pdf file containing the dataset to be processed",
        accepted_types=["pdf"],
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=forms.ClearableFileInput(attrs={"classes": "format-pdf"}),
    )

    # TODO use crops from ...
    # todo custom save method for different formats
