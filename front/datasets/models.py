import shutil
from pathlib import Path
from typing import Dict, List, Tuple
from zipfile import ZipFile
import requests
from PIL import Image as PImage
import traceback
from dataclasses import dataclass

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


class Document:
    """
    A document is a set of images that can be processed together

    NOT A MODEL (for now ?)
    """

    def __init__(
        self, dtype: str = None, uid: str = None, src: str = None, path: Path = None
    ):
        self.dtype = dtype
        self.src = src
        if uid is None:
            self.uid = sanitize_str(src)
        else:
            self.uid = uid

        if path is None:
            path = Path(settings.MEDIA_ROOT) / "documents" / self.uid
        self.path = path

    def to_dict(self) -> Dict:
        return {
            "type": self.dtype,
            "src": self.src,
            "uid": self.uid,
        }

    def is_extracted(self) -> bool:
        return (self.path / "extracted").exists()

    def extract_from_zip(self, source_zip: str | Path):
        """
        Extract the content of the zip file
        """
        extracted_touch = self.path / "extracted"
        if extracted_touch.exists():
            return

        unzip_on_the_fly(source_zip, self.path, [".json", *IMG_EXTENSIONS])

        extracted_touch.touch()

    @property
    def images(self) -> List["Image"]:
        if not hasattr(self, "_images"):
            self._images = self._list_images()
        return self._images

    def _list_images(self) -> List["Image"]:
        if (self.path / "mapping.json").exists():
            with open(self.path / "mapping.json", "r") as f:
                mapping = json.load(f)
            return [
                Image(id=k, path=self.path / "images" / k, src=v, document=self)
                for k, v in mapping.items()
            ]
        else:
            return [
                Image(id=str(p.name), path=p, src=str(p.name), document=self)
                for p in self.path.iterdir()
                if p.suffix.lower() in IMG_EXTENSIONS
            ]


@dataclass
class Image:
    id: str
    src: str
    path: Path
    document: "Document" = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "src": self.src,
            "path": str(self.path),
        }

    @property
    def url(self):
        return f"{settings.MEDIA_URL}{self.path.relative_to(settings.MEDIA_ROOT)}"


class Dataset(AbstractDataset):
    """Set of images to be processed"""

    zip_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)
    iiif_manifests = URLListModelField(
        verbose_name="IIIF Manifest URLs",
        help_text="The URLs to the IIIF manifests of the dataset",
        blank=True,
        null=True,
    )
    pdf_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)

    api_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL where the dataset can be accessed through the API",
    )

    @property
    def crops_path(self) -> Path:
        return self.full_path / "crops"

    @property
    def zip_document(self) -> Document:
        if not hasattr(self, "_zip_document"):
            self._zip_document = Document(
                dtype="zip",
                src=f"{settings.BASE_URL}{self.zip_file.url}",
                path=self.full_path / "unzipped",
            )
        return self._zip_document

    @property
    def pdf_document(self) -> Document:
        if not hasattr(self, "_pdf_document"):
            self._pdf_document = Document(
                dtype="pdf", src=f"{settings.BASE_URL}{self.pdf_file.url}"
            )
        return self._pdf_document

    @property
    def iiif_documents(self) -> List[Document]:
        if not hasattr(self, "_iiif_documents"):
            self._iiif_documents = [
                Document(dtype="iiif", src=url) for url in self.iiif_manifests
            ]
        return self._iiif_documents

    @property
    def documents(self) -> List[Document]:
        docs = []
        if self.zip_file:
            docs.append(self.zip_document)
        if self.pdf_file:
            docs.append(self.pdf_document)
        if self.iiif_manifests:
            docs.extend(self.iiif_documents)
        return docs

    def documents_for_api(self) -> List[Dict]:
        return [doc.to_dict() for doc in self.documents]

    def download_and_extract(self) -> None:
        """
        Download and extract the dataset, from the API or the zip file

        Returns:
            A dictionary of the form {uid: [(filename, fullpath, source(relative or url)))}
            Save the mapping in a json file
        """
        if self.zip_file:
            if not self.zip_document.is_extracted():
                self.zip_document.extract_from_zip(self.zip_file.path)

        if self.iiif_manifests:
            need_extraction = {
                doc.uid: doc for doc in self.iiif_documents if not doc.is_extracted()
            }

            if need_extraction:
                api_info = requests.get(self.api_url).json()

                for doc in api_info["documents"]:
                    if doc["uid"] not in need_extraction:
                        continue
                    need_extraction[doc["uid"]].extract_from_zip(doc["download"])
                    del need_extraction[doc["uid"]]

                if need_extraction:
                    print(f"Could not extract {need_extraction.keys()}")

        if self.pdf_file:
            raise NotImplementedError("PDF extraction not implemented yet")

    def get_images(self) -> List[Document]:
        """
        Check if images have been extracted, download and extract if needed
        """
        self.download_and_extract()
        return self.documents

    def get_path_for_crop(self, crop: Dict, i: int = 0, doc_uid: str = None) -> Path:
        """
        Args:
            crop: A dictionary with the following format: {source: str, crop_id: str}
        """
        crop_id = (
            crop["crop_id"]
            if "crop_id" in crop
            else f"{Path(crop['source']).name}_crop_{i + 1}"
        )
        return self.crops_path / crop.get("doc_uid", doc_uid) / f"{crop_id}.jpg"

    def get_url_for_crop(self, crop: Dict, i: int = 0, doc_uid: str = None) -> str:
        """
        Args:
            crop: A dictionary with the following format: {source: str, crop_id: str}
        """
        return f"{settings.MEDIA_URL}{self.get_path_for_crop(crop, i, doc_uid).relative_to(settings.MEDIA_ROOT)}"

    def get_paths_for_crops(self, crops: List[Dict]) -> List[Path]:
        """
        Args:
            crops: A list of dictionaries with the following format: {source, doc_id, crops: List[Dict]}
        """
        return [
            self.get_path_for_crop(crop, i, im.get("doc_uid", None))
            for im in crops
            for i, crop in enumerate(im.get("crops", []))
        ]

    def get_doc_image_mapping(self) -> Dict[str, Dict[str, Image]]:
        """
        Returns a dictionary of the form {doc_uid: {image_id: Image}}
        """
        return {doc.uid: {im.id: im for im in doc.images} for doc in self.documents}

    def apply_cropping(self, crops: List[Dict]) -> Dict:
        """
        Crop regions from the images of the dataset

        .. code-block:: json

            [
                {
                    "source": "filename", # without extension
                    "crop_id": "crop_id",
                    "crops": [
                        {
                            "relative": { "x1": 0.1, "y1": 0.1, "x2": 0.9, "y2": 0.9 },
                        }
                    ]
                }
            ]

        """
        try:
            self.get_images()
            docs = self.get_doc_image_mapping()
        except Exception as e:
            return {
                "error": f"Error extracting images " + traceback.format_exc(limit=2)
            }

        extracted = 0

        try:
            try:
                for image in crops:
                    image = image.get(0, image)  # Legacy format : single-item lists
                    img_name, crops = image.get("source", ""), image.get("crops", [])
                    doc_uid = image.get("doc_uid", None)
                    imgs = docs.get(doc_uid, None)

                    if imgs is None:
                        return {"error": f"Document {doc_uid} not found"}

                    img = imgs.get(img_name, None)

                    if img is None:
                        return {
                            "error": f"Image {img_name} not found in document {doc_uid}"
                        }

                    crops_path = self.crops_path / img.document.uid
                    crops_path.mkdir(parents=True, exist_ok=True)

                    try:
                        with PImage.open(img.path) as img:
                            for idx, crop in enumerate(crops):
                                crop_id = crop.get("crop_id", None)
                                if crop_id is None:
                                    crop_id = f"{Path(img_name).stem}_crop_{idx + 1}"

                                bbox = crop["relative"]
                                x1, y1, x2, y2 = (
                                    bbox["x1"],
                                    bbox["y1"],
                                    bbox["x2"],
                                    bbox["y2"],
                                )
                                cropped = img.crop(
                                    (
                                        x1 * img.size[0],
                                        y1 * img.size[1],
                                        x2 * img.size[0],
                                        y2 * img.size[1],
                                    )
                                ).convert("RGB")
                                if cropped.size[0] == 0 or cropped.size[1] == 0:
                                    continue

                                cropped.save(
                                    crops_path / f"{crop_id}.jpg",
                                    "JPEG",
                                )
                                extracted += 1

                    except Exception as e:
                        return {
                            "error": f"Error during {img_name} processing: {traceback.format_exc(limit=2)}"
                        }
            except Exception as e:
                return {
                    "error": f"Error during images processing: {traceback.format_exc(limit=2)}"
                }

            # Check if any crops were created
            if extracted == 0:
                return {"error": "No regions were successfully processed"}

        except Exception as e:
            return {
                "error": f"Error during image processing: {traceback.format_exc(limit=2)}"
            }

        return {"success": "Regions processed successfully"}


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
