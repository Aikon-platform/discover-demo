import shutil
from pathlib import Path
from typing import Dict
from zipfile import ZipFile

from django.db import models
from django.conf import settings
import uuid

from .utils import PathAndRename, IMG_EXTENSIONS
from .fields import URLListModelField

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
        # TODO unify and remove usage of zipped_dataset
        """
        return Path(settings.MEDIA_ROOT) / "datasets" / f"{self.id}"

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
    iiif_manifests = URLListModelField(
        verbose_name="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        blank=True,
        null=True,
    )
    pdf_file = models.FileField(upload_to=path_datasets, max_length=500)


class ZippedDataset(AbstractDataset):
    """
    This class is used to store simple datasets made of a single uploaded .zip file
    """

    zip_file = models.FileField(upload_to=path_datasets, max_length=500)

    def extract_images(self):
        try:
            temp_dir = Path(settings.MEDIA_ROOT) / "datasets" / "temp" / f"{self.id}"
            temp_dir.mkdir(parents=True, exist_ok=True)

            target_dir = self.full_path
            is_new = not target_dir.exists()
            if is_new:
                target_dir.mkdir(parents=True, exist_ok=True)

            zip_path = f"{self.full_path}.zip"
            if not Path(zip_path).exists():
                raise ValueError("Zip file not found")

            try:
                with ZipFile(zip_path, "r") as zip_ref:
                    image_files = [
                        f
                        for f in zip_ref.namelist()
                        if Path(f).suffix.lower() in IMG_EXTENSIONS
                    ]
                    if not image_files:
                        raise ValueError("No image files found in zip")

                    if not is_new and len(image_files) == len(
                        list(target_dir.iterdir())
                    ):
                        return list(target_dir.iterdir())

                    zip_ref.extractall(temp_dir)
                    for img_path in image_files:
                        source = temp_dir / img_path
                        target = target_dir / Path(img_path).name
                        if source.exists() and not target.exists():
                            source.rename(target)
            finally:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)

        except Exception as e:
            raise e
        return list(target_dir.iterdir())

    @property
    def images(self) -> dict[str, Path]:
        """
        Check if images have been extracted
        """
        try:
            dataset_dir = self.full_path
            if not dataset_dir.exists() or not list(dataset_dir.iterdir()):
                img_paths = self.extract_images()
            else:
                img_paths = list(dataset_dir.iterdir())
        except Exception as e:
            raise e
        return {fullpath.name: fullpath for fullpath in img_paths}


class CropList(models.Model):
    """
    DB instance + json file to define zones coordinates in a dataset
    base of clustering/similarity/vectorization task
    bounding boxes / full images
    """

    pass
