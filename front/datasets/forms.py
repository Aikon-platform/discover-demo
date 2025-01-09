from django import forms
from django.conf import settings

from .fields import (
    ContentRestrictedFileField,
    URLListField,
    MultipleFileInput,
    URLListWidget,
)
from .models import Dataset

AVAILABLE_FORMATS = [
    ("zip", "ZIP"),
    ("iiif", "IIIF Manifest(s)"),
    ("pdf", "PDF"),
    # ("img", "Image(s)"),
]

MAP_FIELD_FORMAT = {
    "img": "img_files",
    "zip": "zip_file",
    "iiif": "iiif_manifests",
    "pdf": "pdf_file",
}

# TODO make it dynamic
DATASET_FIELDS = [
    "reuse_dataset",
    "dataset",
    "crops",
    "dataset_name",
    "format",
]

for f in AVAILABLE_FORMATS:
    DATASET_FIELDS.append(MAP_FIELD_FORMAT[f[0]])

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
        widget=forms.TextInput(attrs={"extra-class": "new-dataset-field mt-2"}),
    )
    format = forms.ChoiceField(
        label="Type",
        choices=[],  # will be set in __init__
        widget=forms.Select(attrs={"extra-class": "new-dataset-field"}),
    )
    img_files = ContentRestrictedFileField(
        label="Image(s)",
        help_text="Image files containing the dataset to be processed",
        accepted_types=ACCEPTED_IMG_TYPES,
        required=False,
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=MultipleFileInput(
            attrs={
                "multiple": True,
                "extra-class": "format-img format-field new-dataset-field",
            }
        ),
    )
    zip_file = ContentRestrictedFileField(
        label="Zipped Dataset",
        help_text="A .zip file containing the dataset to be processed",
        accepted_types=["application/zip"],
        max_size=settings.MAX_UPLOAD_SIZE,
        required=False,
        widget=forms.ClearableFileInput(
            attrs={"extra-class": "format-zip format-field new-dataset-field"}
        ),
    )
    iiif_manifests = URLListField(
        label="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        required=False,
        widget=URLListWidget(
            attrs={"extra-class": "format-iiif format-field new-dataset-field"}
        ),
    )
    pdf_file = ContentRestrictedFileField(
        label="PDF",
        help_text="A .pdf file containing the dataset to be processed",
        accepted_types=["pdf", "application/pdf"],
        required=False,
        max_size=settings.MAX_UPLOAD_SIZE,
        widget=forms.ClearableFileInput(
            attrs={"extra-class": "format-pdf format-field new-dataset-field"}
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
    class Meta(AbstractDatasetForm.Meta):
        model = Dataset
        fields = AbstractDatasetForm.Meta.fields
