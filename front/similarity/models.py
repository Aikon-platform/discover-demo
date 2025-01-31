import requests
import orjson
import traceback

from django.urls import reverse

from regions.models import AbstractAPITaskOnCrops


class Similarity(AbstractAPITaskOnCrops("similarity")):
    def save_similarity(self, similarity: dict):
        if not self.dataset:
            return
        with open(self.task_full_path / f"{self.dataset.id}.json", "wb") as f:
            f.write(orjson.dumps(similarity))
        self._similarity = similarity

    def _load_similarity(self):
        if not self.dataset:
            return {}
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

            # TODO download annotations file
            # self.save_similarity(output.get("annotations", {}))

            dataset_url = output.get("dataset_url")
            if dataset_url:
                self.dataset.api_url = dataset_url
                self.dataset.save()

            try:
                if self.crops:
                    self.dataset.apply_cropping(self.crops.get_bounding_boxes())

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

    @property
    def similarity_index(self):
        with open(self.result_full_path / "index.json", "r") as f:
            return orjson.loads(f.read())

    @property
    def similarity_matrix(self):
        with open(self.result_full_path / "pairs.json", "r") as f:
            return orjson.loads(f.read())

    def get_similarity_matrix_for_display(self, as_list=True):
        images = self.similarity_index.get("images", [])
        similarities = {}

        for q_idx, s_idx, score, *tr in self.similarity_matrix:
            for img1, img2 in [
                (images[q_idx], images[s_idx]),
                (images[s_idx], images[q_idx]),
            ]:
                if img1["id"] not in similarities:
                    similarities[img1["id"]] = {"query": img1.copy(), "sim": []}
                sim_img = img2.copy()
                sim_img["score"] = float(score)
                similarities[img1["id"]]["sim"].append(sim_img)

        for img in similarities.values():
            img["sim"].sort(key=lambda x: x["score"], reverse=True)

        return list(similarities.values()) if as_list else similarities

    def get_download_json_url(self):
        """Get the URL for downloading crops in a json format"""
        return reverse("similarity:download_json", kwargs={"pk": self.pk})

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
