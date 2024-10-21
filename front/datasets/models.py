from django.db import models
import uuid
import os

from .utils import PathAndRename

path_datasets = PathAndRename("datasets/")


# MODELS
class AbstractDataset(models.Model):
    """
    This class is used to store simple datasets
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=64,
        default="dataset",
        blank=True,
        verbose_name="Dataset name",
        help_text="An optional name to identify this dataset"
    )
    created_on = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True


class ZippedDataset(AbstractDataset):
    """
    This class is used to store simple datasets made of a single uploaded .zip file
    """
    zip_file = models.FileField(upload_to=path_datasets, max_length=500)


class IIIFDataset(AbstractDataset):
    """
    This class is used to store datasets that are available through IIIF
    """
    iiif_manifest = models.URLField(
        max_length=500,
        verbose_name="IIIF Manifest URL",
        help_text="The URL to the IIIF manifest of the dataset"
    )
