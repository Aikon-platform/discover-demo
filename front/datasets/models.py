import shutil
from pathlib import Path
from typing import Dict, List
from zipfile import ZipFile
import requests

from django.db import models
from django.conf import settings
import uuid
import json

from .utils import PathAndRename, IMG_EXTENSIONS, unzip_on_the_fly, sanitize_str
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

    zip_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)
    iiif_manifests = URLListModelField(
        verbose_name="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        null=True,
    )
    pdf_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)

    api_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL where the dataset can be accessed through the API",
    )

    def documents_for_api(self) -> List[Dict]:
        docs = []
        if self.zip_file:
            docs.append(
                {
                    "type": "zip",
                    "src": f"{settings.BASE_URL}{self.zip_file.url}",
                }
            )
        if self.iiif_manifests:
            docs.extend([{"type": "iiif", "src": url} for url in self.iiif_manifests])
        if self.pdf_file:
            docs.append(
                {
                    "type": "pdf",
                    "src": f"{settings.BASE_URL}{self.pdf_file.url}",
                }
            )
        return docs

    def extract_from_zip(self):
        """
        Extract the content of the zip file
        """
        try:
            target_dir = self.full_path / "unzipped"
            is_new = not target_dir.exists()
            if is_new:
                target_dir.mkdir(parents=True, exist_ok=True)

            zip_path = Path(self.zip_file.path)
            if not zip_path.exists():
                raise ValueError("Zip file not found")

            with ZipFile(zip_path, "r") as zip_ref:
                image_files = [
                    f
                    for f in zip_ref.namelist()
                    if Path(f).suffix.lower() in IMG_EXTENSIONS
                ]
                if not image_files:
                    raise ValueError("No image files found in zip")

                if not is_new and len(image_files) == len(list(target_dir.iterdir())):
                    return list(target_dir.iterdir())

                for img_path in image_files:
                    source = zip_ref.open(img_path)
                    target = target_dir / Path(img_path)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(target, "wb") as f:
                        f.write(source.read())
        except Exception as e:
            raise e
        return target_dir.glob("**/*")

    def download_and_extract(self):
        """
        Download and extract the dataset, from the API or the zip file

        Returns:
            A dictionary of the form {uid: {filename: (fullpath, source(relative or url))}}
            Save the mapping in a json file
        """

        def simple_mapping(files, root_path):
            return {
                str(p.relative_to(root_path)): (str(p), str(p.relative_to(root_path)))
                for p in files
            }

        files = {}
        if self.zip_file:
            ffiles = self.extract_from_zip()
            root_path = self.full_path / "unzipped"
            files[
                sanitize_str(f"{settings.BASE_URL}{self.zip_file.url}")
            ] = simple_mapping(ffiles, root_path)

        if self.iiif_manifests:
            # fetch from api
            api_info = requests.get(self.api_url).json()
            for doc in api_info["documents"]:
                if doc["type"] == "iiif":
                    # download zip
                    doc_path = (
                        settings.MEDIA_ROOT
                        / "documents"
                        / sanitize_str(doc["uid"])
                        / "iiif"
                    )
                    ffiles = unzip_on_the_fly(
                        doc["download"], doc_path, [".json", *IMG_EXTENSIONS]
                    )
                    if doc_path / "mapping.json" is not None:
                        with open(doc_path / "mapping.json", "r") as f:
                            mping = json.load(f)
                        for k, v in mping.items():
                            mping[k] = (str(doc_path / "images" / k), v)
                        files[sanitize_str(doc["uid"])] = mping
                    else:
                        files[sanitize_str(doc["uid"])] = simple_mapping(
                            ffiles, doc_path
                        )

        return files

    @property
    def images(self) -> dict[str, Path]:
        """
        Check if images have been extracted
        """
        try:
            dataset_dir = self.full_path
            dataset_dir.mkdir(parents=True, exist_ok=True)
            dfile = dataset_dir / "mapping.json"
            if dfile.exists():
                with open(dfile, "r") as f:
                    img_paths = json.load(f)
            else:
                img_paths = self.download_and_extract()
                with open(dfile, "w") as f:
                    json.dump(img_paths, f)
        except Exception as e:
            raise e
        return img_paths


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
