from logging import root
import shutil
import requests
import uuid
import json
import traceback
import os
import csv

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image as PImage

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import models
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from shared.utils import pprint
from .utils import PathAndRename, IMG_EXTENSIONS, unzip_on_the_fly, sanitize_str
from .fields import URLListModelField

User = get_user_model()
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
    created_by = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, editable=False
    )

    @property
    def full_path(self) -> Path:
        return Path(settings.MEDIA_ROOT) / "datasets" / f"{self.id}"

    django_app_name = "datasets"  # must match INSTALLED_APPS and datasets.url.app_name

    class Meta:
        abstract = True


class Document:
    """
    A document is a set of images that can be processed together

    NOTE: NOT A MODEL (for now ?)
    """

    def __init__(
        self, dtype: str = None, uid: str = None, src: str = None, path: Path = None
    ):
        self.dtype = dtype
        self.src = src or ""
        self.uid = sanitize_str(uid or src)
        self.path = (
            Path(path)
            if path is not None
            else Path(settings.MEDIA_ROOT) / "documents" / self.uid
        )
        self._document_tree = None

    @property
    def mapping_path(self):
        """
        @deprecated: JSON file containing mapping in the form of
        {
            "image_name_front.jpg": "image_name_api.jpg",
            "image_name_front.png": "image_name_api.png",
            "image_name_front.jpeg": "image_name_api.jpeg"
        }
        """
        return self.path / "mapping.json"

    @property
    def images_info_path(self):
        """
        JSON file containing image information
        """
        return self.path / "images.json"

    @property
    def img_path(self):
        """
        Folder containing document extracted images
        """
        return self.path / "images"

    def get_document_tree(self) -> str:
        from .utils import TreeDict

        tree = TreeDict(os.path.join(self.path, "images/"))
        return tree.to_html_pre()

    @property
    def document_tree(self) -> str:
        if self._document_tree is None:
            self._document_tree = self.get_document_tree()
        return self._document_tree

    def to_dict(self) -> Dict:
        return {
            "type": self.dtype,
            "src": str(self.src),
            "uid": str(self.uid),
        }

    def to_json_with_images(self) -> Dict:
        document_dict = self.to_dict()
        document_dict["images"] = [image.to_dict() for image in self.images]
        return document_dict

    def is_extracted(self) -> bool:
        if not self.path.exists():
            self.path.mkdir(parents=True, exist_ok=True)
            return False
        return (self.path / "extracted").exists()

    def extract_from_zip(self, source_zip: str | Path):
        """
        Extract the content of the zip file
        """
        extracted = self.path / "extracted"
        if self.is_extracted():
            return

        extracted_files = unzip_on_the_fly(
            source_zip, self.path, [".json", *IMG_EXTENSIONS]
        )

        if len(extracted_files) == 0:
            raise Exception("No files were extracted")

        extracted.touch()

    @property
    def images(self) -> List["Image"]:
        if not hasattr(self, "_images"):
            self._images = self._list_images()
        return self._images

    def _list_img_dir(self):
        return [
            Image(
                id=str(p.relative_to(self.img_path)),
                path=p,
                src=str(p.relative_to(self.img_path)),
                document=self,
            )
            for p in self.img_path.rglob("*")
            if p.is_file() and p.suffix.lower() in IMG_EXTENSIONS
        ]

    def _legacy_list_img_mapping(self):
        try:
            with open(self.mapping_path, "r") as f:
                mapping = json.load(f)
            return [
                Image(id=k, path=self.img_path / k, src=v, document=self)
                for k, v in mapping.items()
            ]
        except Exception:
            return []

    def _list_images(self) -> List["Image"]:
        if self.mapping_path.exists():
            return self._legacy_list_img_mapping()

        if self.images_info_path.exists():
            with open(self.images_info_path, "r") as f:
                data = json.load(f)
            return [Image.from_dict(im, self) for im in data]

        return self._list_img_dir()


@dataclass
class Image:
    id: str
    src: str
    path: Path
    metadata: Optional[Dict[str, str]] = None
    document: "Document" = None

    def to_dict(self, relpath: Path = None) -> Dict:
        if relpath is None:
            relpath = self.document.path
        return {
            "id": self.id,
            "src": str(self.src),
            "path": str(self.path.relative_to(relpath)),
            "metadata": self.metadata,
            "url": self.url,
        }

    @classmethod
    def from_dict(
        cls, data: Dict, document: "Document", relpath: Path = None
    ) -> "Image":
        if relpath is None:
            relpath = document.path
        return cls(
            id=data["id"],
            src=data["src"],
            path=relpath / data["path"],
            metadata=data.get("metadata", None),
            document=document,
        )

    @property
    def url(self):
        return f"{settings.MEDIA_URL}{self.path.relative_to(settings.MEDIA_ROOT)}"


class Dataset(AbstractDataset):
    """Set of images to be processed"""

    # TODO upload to documents/ instead??
    zip_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)
    iiif_manifests = URLListModelField(
        blank=True,
        null=True,  # keep manifest url somewhere?
    )
    pdf_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)
    img_files = models.FileField(upload_to=path_datasets, max_length=500, null=True)

    metadata_file = models.FileField(upload_to=path_datasets, max_length=500, null=True)

    api_url = models.URLField(
        null=True,
        blank=True,
        help_text="The URL where the dataset can be accessed through the API",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._images = None

    def __str__(self) -> str:
        return f"{self.name} #{self.id}" if self.name else f"Dataset #{self.id}"

    def get_absolute_url(self):
        # TODO change when detailed view for dataset is created
        key = self.pk
        return reverse(f"datasets:view", kwargs={"pk": self.pk})

    @property
    def format(self):
        if self.zip_file:
            return "zip"
        if self.pdf_file:
            return "pdf"
        if self.iiif_manifests:
            return "iiif"
        if self.img_files:
            return "img"
        return "unknown"

    def save(self, *args, **kwargs):
        if not self.name:
            file_field = self.zip_file or self.pdf_file or self.img_files
            if file_field:
                self.name = Path(file_field.name).name
            elif self.iiif_manifests:
                self.name = f"Manifests {Path(self.iiif_manifests[0]).name} ({len(self.iiif_manifests)})"
            else:
                self.name = "Dataset"

        super().save()

    @property
    def crops_path(self) -> Path:
        return self.full_path / "crops"

    @property
    def zip_document(self) -> Document:
        if not hasattr(self, "_zip_document"):
            self._zip_document = Document(
                dtype="zip",
                src=f"{settings.BASE_URL}{self.zip_file.url}",
                # path=self.full_path / "unzipped",
            )
        return self._zip_document

    @property
    def pdf_document(self) -> Document:
        if not hasattr(self, "_pdf_document"):
            self._pdf_document = Document(
                dtype="pdf",
                src=f"{settings.BASE_URL}{self.pdf_file.url}",
                # path=self.full_path / "pdf",
            )
        return self._pdf_document

    @property
    def iiif_documents(self) -> List[Document]:
        if not hasattr(self, "_iiif_documents"):
            self._iiif_documents = [
                Document(
                    dtype="iiif",
                    src=url,
                    # path=self.full_path / f"iiif_{i}",
                )
                for url in self.iiif_manifests
            ]
        return self._iiif_documents

    @property
    def img_documents(self) -> List[Document]:
        if not hasattr(self, "_img_documents"):
            self._img_documents = [
                # Document(dtype="img", src=f"{settings.BASE_URL}{img.url}")
                # for img in self.img_files
            ]
        return self._img_documents

    @property
    def documents(self) -> List[Document]:
        docs = []
        if self.zip_file:
            docs.append(self.zip_document)
        if self.pdf_file:
            docs.append(self.pdf_document)
        if self.iiif_manifests:
            docs.extend(self.iiif_documents)
        if self.img_documents:
            docs.extend(self.img_documents)
        return docs

    @property
    def image_count(self) -> int:
        """
        number of in a Dataset. `Dataset.get_images()` also allows to get
        the number of images but may trigger `Dataset.download_and_extract()`,
        which takes time, while `image_count` is only used in templates
        """
        return sum(len(doc.images) for doc in self.documents)

    def documents_for_api(self) -> List[Dict]:
        return [doc.to_dict() for doc in self.documents]

    def download_from_api(self, doc_to_extract=None) -> None:
        if len(doc_to_extract) == 0:
            return

        """
        api_info = {
            'documents': [{
                'download': 'API_URL/datasets/document/<doc_type>/<doc_uid>/download',
                'src': 'FRONT_URL/media/datasets/<original_file>.<ext>',
                'type': '<doc_type>',
                'uid': '<doc_uid>',
                'url': 'API_URL/datasets/document/<doc_type>/<doc_uid>'
            }, {...}],
            'uid': '<dataset_uid>',
            'url': '<dataset_url>'
        }
        """
        try:
            api_info = requests.get(self.api_url).json()
        except Exception as e:
            print(f"Error fetching dataset info: {e}")
            return

        for doc in api_info.get("documents", []):
            if doc["uid"] not in doc_to_extract:
                continue

            doc_to_extract[doc["uid"]].extract_from_zip(doc["download"])
            del doc_to_extract[doc["uid"]]

        if doc_to_extract:
            print(f"Could not extract {doc_to_extract.keys()}")

        # process metadata
        self.clean_metadata()

    def download_and_extract(self) -> None:
        """
        Download and extract the dataset, from the API or the zip file

        Returns:
            A dictionary of the form {uid: [(filename, fullpath, source(relative or url)))}
            Save the mapping in a json file
        """
        need_extraction = {
            doc.uid: doc for doc in self.documents if not doc.is_extracted()
        }
        self.download_from_api(need_extraction)

    def get_images(self) -> List[Document]:
        """
        Check if images have been extracted, download and extract if needed
        """
        if not self._images:
            self.download_and_extract()
            self._images = [im for doc in self.documents for im in doc.images]
        return self._images

    def get_path_for_crop(self, crop: Dict, i: int = 0, doc_uid: str = None) -> Path:
        """
        Args:
            crop: A dictionary with the following format: {source: str, crop_id: str}
            i: Index of the crop
            doc_uid: The uid of the document
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
            i: Index of the crop
            doc_uid: The uid of the document
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
        if not self._images:
            self.get_images()
        return {doc.uid: {im.id: im for im in doc.images} for doc in self.documents}

    def get_doc_image_mapping_json(self) -> Dict[str, Dict[str, Dict]]:
        """
        same as ``get_doc_image_mapping``, but returns a valid JSON instead of python types.
        the contents of each `document` are returned as a list of tuples to be able to order
        images by their filename alphanumerically.
        """
        # sorted_document_images = lambda doc: (
        #     sorted(
        #         [(im.id, im.to_dict()) for im in doc.images], key=lambda t: t[1]["path"]
        #     )
        # )
        return {
            doc.uid: {im.id: im.to_dict() for im in doc.images}
            for doc in self.documents
        }

    def add_urls_to_serialization(self, serialized: dict, crops: bool = False):
        """
        Add the URL field to the images in the serialized description from the API
        Modifies the dict in place
        """
        doc_image_mapping = self.get_doc_image_mapping()

        for im in serialized.get("images", []):
            if crops:
                im["url"] = self.get_url_for_crop(
                    {"crop_id": im["id"]}, doc_uid=im["doc_uid"]
                )
            else:
                img = doc_image_mapping.get(im["doc_uid"], {}).get(im["id"], None)
                if img:
                    im["url"] = img.url

    def clear_dataset(self) -> Dict:
        """
        Delete the dataset files (crops included)
        """
        if zipf := self.zip_file:
            zipf.delete(save=False)
        if pdf := self.pdf_file:
            pdf.delete(save=False)
        if imgs := self.img_files:
            # TODO check if it works
            [img.delete(save=False) for img in imgs]

        for doc in self.documents:
            shutil.rmtree(doc.path, ignore_errors=True)
            # TODO delete effectively (do not work for certain type of document)

        # TODO delete dataset from API ⚠️⚠️⚠️⚠️

        shutil.rmtree(self.full_path, ignore_errors=True)

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
            # download the images if not already done
            docs = self.get_doc_image_mapping()
        except Exception as e:
            return {
                "error": f"Error extracting images:\n{traceback.format_exc(limit=2)}"
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
                                crop_id = crop.get("crop_id", "")

                                if not crop_id:
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

                                crop_file = crops_path / f"{crop_id}.jpg"
                                crop_file.parent.mkdir(parents=True, exist_ok=True)

                                cropped.save(
                                    crop_file,
                                    "JPEG",
                                )
                                extracted += 1

                    except Exception as e:
                        return {
                            "error": f"Error during {img_name} processing:\n{traceback.format_exc(limit=2)}"
                        }
            except Exception as e:
                return {
                    "error": f"Error during images processing:\n{traceback.format_exc(limit=2)}"
                }

            # Check if any crops were created
            if extracted == 0:
                return {
                    "error": f"No regions were successfully processed in:\n{pprint(crops)}"
                }

        except Exception as e:
            return {
                "error": f"Error during image processing: {traceback.format_exc(limit=2)}"
            }

        return {"success": "Regions processed successfully"}

    def get_tasks_for_prefix(self, prefix) -> List:
        return (
            list(getattr(self, f"{prefix}_tasks").all())
            if hasattr(self, f"{prefix}_tasks")
            else []
        )

    @property
    def tasks(self) -> List:
        t = []
        for task_prefix in settings.DEMO_APPS:
            if len(tasks := self.get_tasks_for_prefix(task_prefix)):
                t += tasks
        return t

    @property
    def task_prefixes(self) -> List[str]:
        """
        a list of all tasks prefixes on which tasks have been run on this dataset
        """
        return [
            prefix
            for prefix in settings.DEMO_APPS
            if len(self.get_tasks_for_prefix(prefix))
        ]

    @property
    def tasks_by_prefix(self) -> List[Tuple[str, List]]:
        """
        same as `self.tasks`, but tasks are grouped by type/prefix.
        Returns:
            [
                [ task_prefix, [List,of,tasks,for,prefix] ]
            ]
        """
        prefixes = settings.DEMO_APPS
        grouped_tasks = [
            (task_prefix, tasks)
            for task_prefix in prefixes
            if len(tasks := self.get_tasks_for_prefix(task_prefix))
        ]
        # order groups by descending number of tasks
        return sorted(grouped_tasks, key=lambda task_group: -len(task_group[1]))

    def get_tasks_by_prop(self, prop: str) -> Dict:
        info = {}
        for task in self.tasks:
            prop_value = getattr(task, prop)
            if prop_value not in info:
                info[prop_value] = []
            info[prop_value].append(task)
        return info

    ## Metadata
    @property
    def cleaned_metadata_path(self) -> Path:
        if self.metadata_file:
            return self.full_path / "metadata.json"
        return None
    
    @property
    def cleaned_metadata_url(self) -> str:
        path = self.cleaned_metadata_path
        if path:
            return f"{settings.MEDIA_URL}{path.relative_to(Path(settings.MEDIA_ROOT))}"
        return None

    def clean_metadata(self):
        """
        Create a clean version of the metadata csv file, ready for display
        """
        if not self.metadata_file:
            return
        
        with open(self.metadata_file.path, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        labels = rows[0]
        normalized_labels = [label.lower().strip() for label in labels]

        # Find title and description
        col_title = 0
        col_desc = 1
        col_url = None
        if "title" in normalized_labels:
            col_title = normalized_labels.index("title")
        elif "name" in normalized_labels:
            col_title = normalized_labels.index("name")
        if "description" in normalized_labels:
            col_desc = normalized_labels.index("description")
        elif "document" in normalized_labels:
            col_desc = normalized_labels.index("document")
        if "url" in normalized_labels:
            col_url = normalized_labels.index("url")

        def clean_source(row):
            source = {
                "name": row[col_title-1],
                "description": row[col_desc-1],
                "url": row[col_url-1] if col_url is not None else None,
                "metadata": {
                    k: v for i, (k, v) in enumerate(zip(labels[1:], row)) if normalized_labels[i+1] not in ["title", "description", "url"]
                }
            }
            return source

        sources = {
            key: clean_source(row)
            for key, *row in rows[1:]
        }
        max_keylen = max(len(key) for key in sources.keys())

        images = [im for doc in self.documents for im in doc.images]
        matched_sources = {key: False for key in sources.keys()}

        def best_match(path):
            # returns longest prefix in sources
            for k in range(max_keylen, 0, -1):
                if path[:k] in sources:
                    matched_sources[path[:k]] = True
                    return path[:k]
            return None

        image_matches = {
            str(im.src): best_match(str(im.src)) for im in images
        }

        if not any(matched_sources.values()):
            print("Some metadata keys were not matched:", [k for k, v in matched_sources.items() if not v])
        
        self.cleaned_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cleaned_metadata_path, "w") as f:
            json.dump(
                {
                    "sources": {k:v for k,v in sources.items() if matched_sources[k]}, 
                    "mapping": image_matches
                }, f)

@receiver(pre_delete, sender=Dataset)
def delete_dataset_files(sender, instance: Dataset, **kwargs):
    try:
        instance.clear_dataset()
    except Exception as e:
        print("Error deleting dataset files", e, traceback.format_exc(limit=2))


class CropList(models.Model):
    """
    TODO delete ? for now Regions is used
    DB instance + json file to define zones coordinates in a dataset
    base of clustering/similarity/vectorization task
    bounding boxes / full images
    """

    pass
