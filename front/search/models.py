import traceback
import uuid
from pathlib import Path
import requests
from typing import Optional
from uuid import uuid4
import re

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
import orjson

from shared.utils import sanitize_for_regex
from regions.models import AbstractAPITaskOnCrops
from datasets.models import Dataset


User = get_user_model()


class Index(models.Model):
    """
    A model that stores information about a searchable image index
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="search_index"
    )

    name = models.CharField(max_length=511, blank=True, default=None, unique=True)
    description = models.TextField(blank=True, default="")

    index_id = models.CharField(max_length=511, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    from_task = models.OneToOneField(
        "Indexing", on_delete=models.CASCADE, related_name="index"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="search_index"
    )

    use_transpositions = models.BooleanField(default=False, blank=True)
    public = models.BooleanField(default=False, blank=True)

    feat_net = models.CharField(max_length=511, blank=True, default="")

    def __str__(self):
        return f"Index {self.name}"

    @property
    def index_path(self):
        return Path(settings.MEDIA_ROOT) / f"search/index-{self.id}.json"

    @property
    def index_url(self):
        return f"{settings.MEDIA_URL}search/index-{self.id}.json"

    @classmethod
    def available_indexes(cls, user: Optional[User]=None):
        filt = Q(public=True)
        if user:
            filt = filt | Q(owner=user)
        return cls.objects.filter(filt)

    @classmethod
    def get_index_names(cls, index_pk) -> list[str]:
        # filter out pk: in the case of updates, the Index is aldready in the DB but
        # we don't want to autoincrement its name => filter it out
        index_names = cls.objects.filter(~Q(pk=index_pk)).values_list(("name"))
        return [ n[0] for n in index_names]

    def set_index(self, index: dict):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "wb") as f:
            f.write(orjson.dumps(index))

    def get_index(self):
        if not self.index_path.exists():
            return None
        with open(self.index_path, "rb") as f:
            return orjson.loads(f.read())

    def set_index_name(self) -> "Index":
        """
        ensure the index name is unique by auto-incrementing it, if necessary
        """
        index_name = self.name
        existing_index_names = self.get_index_names(self.pk)

        # the `name` is used in Watermarks forms to select an index
        # by defining its name in the URL query string => if no name
        # is given, define a default name.
        if not index_name:
            index_name = f"index-{uuid4()}"
            self.name = index_name
            return self

        # index_name is new => all good
        if index_name not in existing_index_names:
            self.name = index_name
            return self

        # since name must be unique, if another index has the same name,
        # autoincrement the index name. structure: {index_name}-{n}.
        index_name = sanitize_for_regex(index_name)
        rgx_autoincrement = re.compile(fr"^({index_name})-(\d+)$")
        # keep only the incremented index names from `existing_index_names`
        incremented = [
            rgx_autoincrement.match(name)
            for name in existing_index_names
        ]
        incremented = [ m for m in incremented if m is not None ]
        # index_name is in the db, but no pre-existing autoincrement => just add 1.
        if not len(incremented):
            index_name = f"{index_name}-1"
            self.name = index_name
            return self
        # index_name is in the db and has been autoincremented => re-autoincrement
        n_all = [ int(m[2]) for m in incremented ]
        n_max = max(n_all)
        index_name = f"{index_name}-{n_max+1}"
        self.name = index_name
        return self


class Indexing(AbstractAPITaskOnCrops("search/indexing")):
    def __str__(self):
        if not self.name:
            param = getattr(self, "parameters", {})
            feat_net = param.get("feat_net", None)
            return f"Search Indexing{f' ({feat_net})' if feat_net else ''}"
        return str(self.name)

    def save_output(self, output: dict):
        """
        Save index data to file
        """
        if not self.dataset:
            return

        index_id = output.get("metadata", {}).get("index_id", None)
        if not index_id:
            raise ValueError("Index ID not found in output")

        self.index = Index.objects.create(
            dataset=self.dataset,
            name=self.name,
            index_id=index_id,
            from_task=self,
            owner=self.requested_by,
            use_transpositions=len(self.parameters.get("transpositions", ["none"])) > 2,
            feat_net=self.parameters.get("feat_net", ""),
        )

        with open(self.task_full_path / f"{self.index.index_id}.json", "wb") as f:
            f.write(orjson.dumps(output))

    def _load_output(self):
        if not self.dataset:
            return {}
        with open(self.task_full_path / f"{self.index.index_id}.json", "rb") as f:
            return orjson.loads(f.read())

    @property
    def output(self):
        if not hasattr(self, "_output"):
            self._output = self._load_output()
        return self._output

    def prepare_sim_browser(self):
        """
        Prepare index data for browser
        """
        if not self.dataset:
            return

        output = self.output

        index = output.get("index", {})
        self.dataset.add_urls_to_serialization(index, self.crops)
        self.index.set_index(index)

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return

            results_url = output.get("results_url", None)
            if not results_url:
                self.on_task_error({"error": "No results URL"})
                return

            result = requests.get(results_url)
            if result.status_code != 200:
                self.on_task_error({"error": "Failed to get results"})
                return

            result_json = result.json()

            self.save_output(result_json)

            try:
                # Prepare dataset and crop images
                if not self.prepare_dataset_from_api(output):
                    return

                # Prepare index data for browser
                self.prepare_sim_browser()

            except Exception as e:
                self.on_task_error({"error": traceback.format_exc()})
                return

        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)


class Query(AbstractAPITaskOnCrops("search/query")):
    """
    Query images on a given indexed dataset
    """

    target_index = models.ForeignKey(
        Index, on_delete=models.CASCADE, related_name="queries"
    )

    def __str__(self):
        if not self.name:
            return f"Search Query on index {self.target_index.index_id}"
        return self.name

    def get_task_kwargs(self):
        kwargs = super().get_task_kwargs()
        return {
            **kwargs,
            "parameters": {
                **(kwargs["parameters"] or {}),
                "index_id": self.target_index.index_id,
            },
        }

    def save_output(self, output: dict):
        with open(self.task_full_path / "output.json", "wb") as f:
            f.write(orjson.dumps(output))

    @property
    def output(self):
        if not hasattr(self, "_output"):
            self._output = self._load_output()
        return self._output

    def _load_output(self):
        if not self.dataset:
            return {}
        with open(self.task_full_path / "output.json", "rb") as f:
            return orjson.loads(f.read())

    @property
    def result_url(self):
        return f"{self.result_media_url}/result.json"

    @property
    def result_path(self):
        return self.result_full_path / "result.json"

    def prepare_sim_browser(self):
        query = self.output.get("query", {})
        pairs = self.output.get("pairs", [])

        self.dataset.add_urls_to_serialization(query, self.crops)

        with open(self.result_path, "wb") as f:
            f.write(orjson.dumps({"query": query, "pairs": pairs}))

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return

            results_url = output.get("results_url", None)
            if not results_url:
                self.on_task_error({"error": "No results URL"})
                return

            result = requests.get(results_url)
            if result.status_code != 200:
                self.on_task_error({"error": "Failed to get results"})
                return

            result_json = result.json()

            self.save_output(result_json)

            try:
                # Prepare dataset and crop images
                if not self.prepare_dataset_from_api(output):
                    return

                # Prepare index data for browser
                self.prepare_sim_browser()

            except Exception as e:
                self.on_task_error({"error": traceback.format_exc()})
                return

        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)


@receiver(pre_save, sender=Index)
def set_name(sender, **kwargs):
    """
    before creating/updating an Index, ensure its name is unique
    by auto-incrementing it if necessary
    """
    instance: Index = kwargs.get("instance")
    instance = instance.set_index_name()
    return instance

