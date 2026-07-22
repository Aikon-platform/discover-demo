from django.db import models

from tasking.models import AbstractAPITaskOnDataset


class Paleography(AbstractAPITaskOnDataset("paleography")):
    """
    "Paleography" task (D1): processing of a line-image dataset
    together with their transcriptions.

    Base = AbstractAPITaskOnDataset (like Regions): IMAGES are extracted by the
    API (the front has no local zip->images path, `Dataset.download_from_api`
    requires `dataset.api_url`). The API endpoint /paleography/start only
    creates the dataset (no vision algorithm).

    TRANSCRIPTIONS belong to the DATASET, not to the task (architecture
    validated with Paul & Segolene): extracted from the zip at import time
    (`Dataset.extract_transcriptions`, triggered from the form) and persisted
    under MEDIA_ROOT. The task only reads them and checks they are present.
    """

    class Meta:
        verbose_name = "Paleography"
        ordering = ["-requested_on"]

    def __str__(self):
        name = self.name or "Paleography"
        return (
            f"{name} on {self.dataset.name}" if self.dataset else f"{name} #{self.pk}"
        )

    @property
    def transcriptions(self) -> dict:
        """
        Transcriptions of the associated dataset (read-only).
        Mapping { "<sous-dossier>/<radical>": "<transcription>" }.
        """
        return self.dataset.get_transcriptions() if self.dataset else {}

    @property
    def has_transcriptions(self) -> bool:
        return bool(self.transcriptions)

    def on_task_success(self, data):
        """
        Called when the API notifies SUCCESS (dataset created + images extracted).

        The .txt ingestion already happened at dataset import time: here we
        only check that transcriptions are available before validating the task
        (meeting decision: when a paleography treatment is launched, we verify
        that the transcriptions are indeed available).
        """
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        output = (data or {}).get("output", {})

        # sets self.dataset.api_url from output["dataset_url"]
        if not self.prepare_dataset_from_api(output):
            return

        if not self.dataset.has_transcriptions:
            self.on_task_error(
                {
                    "error": "This dataset is not flagged as having  "
                    'transcriptions: check "Has transcriptions" when importing.'
                }
            )
            return

        if not self.transcriptions:
            self.on_task_error(
                {
                    "error": "No transcription found in the zip: each image must "
                    "come with a .txt file of the same name, in the same folder."
                }
            )
            return
    
        report = self.dataset.transcriptions_report()
        if report:
            self.write_log(f"Dataset import warnings: {report}\n")
        return super().on_task_success(data)
