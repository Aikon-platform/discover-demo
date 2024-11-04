from pathlib import Path

from django.db import models
from django.conf import settings
import uuid

from .utils import PathAndRename

path_datasets = PathAndRename("datasets/")


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
        help_text="An optional name to identify this dataset",
    )
    created_on = models.DateTimeField(auto_now_add=True, editable=False)

    @property
    def full_path(self) -> Path:
        """
        Full path to the dataset zip file
        # TODO unify and remove usage of zipped_dataset
        """
        return Path(settings.MEDIA_ROOT) / "datasets" / f"{self.pk}.zip"
        # return Path(settings.MEDIA_ROOT) / "datasets" / f"{self.id}.zip"

    class Meta:
        abstract = True


class Dataset(AbstractDataset):
    """Set of images to be processed"""

    format = models.CharField(
        max_length=64,
        default="dataset",
        blank=True,
        verbose_name="Dataset type",
        help_text="The type of dataset",
    )

    zip_file = models.FileField(upload_to=path_datasets, max_length=500)
    iiif_manifest = models.URLField(
        max_length=500,
        verbose_name="IIIF Manifest URL",
        help_text="The URL to the IIIF manifest of the dataset",
    )
    pdf_file = models.FileField(upload_to=path_datasets, max_length=500)


class ZippedDataset(AbstractDataset):
    """
    This class is used to store simple datasets made of a single uploaded .zip file
    """

    zip_file = models.FileField(upload_to=path_datasets, max_length=500)


class CropList(models.Model):
    """
    DB instance + json file to define zones coordinates in a dataset
    base of clustering/similarity/vectorization task
    bounding boxes / full images
    """

    pass
