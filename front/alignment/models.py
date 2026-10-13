import requests
import orjson
import traceback

from django.urls import reverse

from regions.models import AbstractAPITaskOnCrops


class Alignment(AbstractAPITaskOnCrops("alignment")):
    def __str__(self):
        if not self.name:
            param = getattr(self, "parameters", {})
            method = param.get("method", "sift+ransac")
            return f"{method} alignment"
        return self.name

    def save(self, *args, **kwargs):
        super().save()

    def save_alignment_results(self, output: dict):
        if not self.dataset:
            return

        result_urls = output.get("results_url", [])

        if len(result_urls) > 1:
            raise ValueError("Multiple alignment results not supported")

        alignment_results = {}
        
        for result in result_urls:
            result_url = result.get("result_url", "")
            try:
                response = requests.get(result_url, stream=True)
                response.raise_for_status()
                alignment_results = response.json()
                break
            except Exception as e:
                raise ValueError(f"Could not retrieve alignment result from {result_url}: {e}")

        # Save to a JSON file for the dataset
        with open(self.task_full_path / f"{self.dataset.id}.json", "wb") as f:
            f.write(orjson.dumps(alignment_results))
        self._alignment_results = alignment_results

    def _load_alignment_results(self):
        if not self.dataset:
            return {}
        try:
            with open(self.task_full_path / f"{self.dataset.id}.json", "rb") as f:
                return orjson.loads(f.read())
        except FileNotFoundError:
            return {}

    @property
    def alignment_results(self):
        if not hasattr(self, "_alignment_results"):
            self._alignment_results = self._load_alignment_results()
        return self._alignment_results

    def on_task_success(self, data):
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        if data is not None:
            output = data.get("output", {})
            if not output:
                self.on_task_error({"error": "No output data"})
                return
            self.save_alignment_results(output)

            try:
                if not self.prepare_dataset_from_api(output):
                    return

                # Prepare results for display
                self.prepare_alignment_display()

            except Exception as e:
                self.on_task_error({"error": traceback.format_exc()})
                return

        else:
            self.on_task_error({"error": "No output data"})
            return

        return super().on_task_success(data)

    def prepare_alignment_display(self):
        """
        Prepare alignment results for frontend display.
        """
        # The main result file that the frontend will use for display
        if self.alignment_results:
            self.dataset.add_urls_to_serialization(
                self.alignment_results.get("index", {}), self.crops
            )
            with open(self.result_full_path / "alignment.json", "wb") as f:
                f.write(orjson.dumps(self.alignment_results))

    @property
    def alignment_display_url(self):
        return f"{self.result_media_url}/alignment.json"

    def get_alignment_results_for_display(self):
        return self.alignment_results

    def get_download_json_url(self):
        """Get the URL for downloading alignment results in JSON format"""
        return reverse("alignment:download_json", kwargs={"pk": self.pk})
