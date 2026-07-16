import json

from django.db import models

from tasking.models import AbstractAPITaskOnDataset
from .transcription import pair_transcriptions_from_zip


class Paleography(AbstractAPITaskOnDataset("paleography")):
    """
    Tâche "paléographie" (D1) : upload d'un dataset d'images de lignes + transcriptions.

    Base = AbstractAPITaskOnDataset (comme Regions), PAS la base non-API :
      - les IMAGES sont extraites par l'API (le front n'a pas de chemin zip->images
        local : `Dataset.download_from_api` exige `dataset.api_url`) ;
      - décision réunion #3 : base API, calquée sur AbstractAPITaskOnCrops.
    "Pas de traitement" = l'endpoint API /paleography/start ne fait que créer le
    dataset (aucun algo de vision).

    Les TRANSCRIPTIONS, elles, sont ingérées CÔTÉ FRONT (décision #6) : on relit le
    zip uploadé (que l'API ignore, cf. extract_from_zip qui ne garde que .json+images)
    et on apparie .txt <-> image, puis on persiste sous MEDIA_ROOT (décision #7).
    """

    # Mapping { "<dossier>/<radical>": "<transcription>" } des paires retenues
    transcriptions = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Paléographie"
        ordering = ["-requested_on"]

    def __str__(self):
        name = self.name or "Paléographie"
        return (
            f"{name} on {self.dataset.name}"
            if self.dataset
            else f"{name} #{self.pk}"
        )

    def on_task_success(self, data):
        """
        Appelé quand l'API notifie SUCCESS (dataset créé + images extraites).
        On y branche l'ingestion des transcriptions, côté front, depuis le zip.
        Structure mirroir de Regions.on_task_success.
        """
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        output = (data or {}).get("output", {})

        # renseigne self.dataset.api_url à partir de output["dataset_url"]
        if not self.prepare_dataset_from_api(output):
            return

        # --- Ingestion des transcriptions (CÔTÉ FRONT, depuis le zip uploadé) ---
        try:
            zip_field = self.dataset.zip_file
            if not zip_field:
                self.on_task_error(
                    {"error": "Dataset sans zip : l'upload paléographie doit être un Zip (décision #4)."}
                )
                return

            result = pair_transcriptions_from_zip(zip_field.path)
            self.transcriptions = result["pairs"]

            # Persistance sous MEDIA_ROOT, comme les outputs de tâches (décision #7)
            with open(self.task_full_path / f"{self.dataset.id}.json", "w") as f:
                json.dump(self.transcriptions, f, ensure_ascii=False)
        except Exception as e:
            self.on_task_error({"error": f"Ingestion des transcriptions échouée:\n{e}"})
            return

        return super().on_task_success(data)

    @property
    def has_transcriptions(self) -> bool:
        return bool(self.transcriptions)
