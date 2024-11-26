from typing import Dict, Any
import requests
import orjson
import traceback

from django.db import models

from tasking.models import AbstractAPITaskOnDataset

from regions.models import Regions


class Similarity(AbstractAPITaskOnDataset("similarity")):
    crops = models.ForeignKey(
        Regions,
        verbose_name="Use crops from...",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="similarity_crops",
    )

    def get_task_kwargs(self) -> Dict[str, Any]:
        """Returns kwargs for the API task"""
        kwargs = super().get_task_kwargs()
        if self.crops:
            kwargs["crops"] = self.crops.get_bounding_boxes()
        return kwargs

    @classmethod
    def get_available_models(cls):
        try:
            response = requests.get(f"{cls.api_endpoint_prefix}/models")
            response.raise_for_status()
            models = response.json()
            if not models:
                return [("", "No models available")]
            # models = { "ref": { "name": "Display Name", "model": "filename", "desc": "Description" }, ... }
            return [
                (info["model"], f"{info['name']} ({info['desc']})")
                for info in models.values()
            ]
        except Exception as e:
            return [("", f"Error fetching models: {e}")]

    def save_similarity(self, similarity: dict):
        with open(self.task_full_path / f"{self.dataset.id}.json", "wb") as f:
            f.write(orjson.dumps(similarity))
        self._similarity = similarity

    def _load_similarity(self):
        with open(self.task_full_path / f"{self.dataset.id}.json", "rb") as f:
            return orjson.loads(f.read())

    @property
    def similarity(self):
        if not hasattr(self, "_similarity"):
            self._similarity = self._load_similarity()
        return self._similarity

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return

            self.save_similarity(output.get("annotations", {}))

            dataset_url = output.get("dataset_url")
            if dataset_url:
                self.dataset.api_url = dataset_url
                self.dataset.save()

            try:
                if self.crops:
                    result = self.dataset.apply_cropping(
                        self.crops.get_bounding_boxes()
                    )

                self.prepare_sim_browser()

            except Exception as e:
                self.on_task_error({"error": traceback.format_exc()})
                return

        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)

    @property
    def index_url(self):
        return f"{self.result_media_url}/index.json"

    @property
    def similarity_matrix_url(self):
        return f"{self.result_media_url}/pairs.json"

    def prepare_sim_browser(self):
        sim_index = self.similarity.get("index", {})
        sim_pairs = self.similarity.get("pairs", [])

        doc_image_mapping = self.dataset.get_doc_image_mapping()

        for im in sim_index.get("images", []):
            if self.crops:
                im["url"] = self.dataset.get_url_for_crop(
                    {"crop_id": im["id"]}, doc_uid=im["doc_uid"]
                )
            else:
                img = doc_image_mapping.get(im["doc_uid"], {}).get(im["id"], None)
                if img:
                    im["url"] = img.url

        with open(self.result_full_path / "index.json", "wb") as f:
            f.write(orjson.dumps(sim_index))

        with open(self.result_full_path / "pairs.json", "wb") as f:
            f.write(orjson.dumps(sim_pairs))
