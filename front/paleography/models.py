from django.db import models

from tasking.models import AbstractAPITaskOnDataset


class Paleography(AbstractAPITaskOnDataset("paleography")):
    """
    Tâche "paléographie" (D1) : traitement d'un dataset d'images de lignes
    accompagnées de leurs transcriptions.

    Base = AbstractAPITaskOnDataset (comme Regions) : les IMAGES sont extraites par
    l'API (le front n'a pas de chemin zip->images local, `Dataset.download_from_api`
    exige `dataset.api_url`). L'endpoint API /paleography/start ne fait que créer le
    dataset (aucun algo de vision).

    Les TRANSCRIPTIONS appartiennent au DATASET, pas à la tâche (archi validée avec
    Paul & Ségolène) : elles sont extraites du zip à l'import
    (`Dataset.extract_transcriptions`, déclenché depuis le formulaire) et persistées
    sous MEDIA_ROOT. La tâche se contente de les lire et de vérifier qu'elles sont là.
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
        Transcriptions du dataset associé (lecture seule).
        Mapping { "<sous-dossier>/<radical>": "<transcription>" }.
        """
        return self.dataset.get_transcriptions() if self.dataset else {}

    @property
    def has_transcriptions(self) -> bool:
        return bool(self.transcriptions)

    def on_task_success(self, data):
        """
        Appelé quand l'API notifie SUCCESS (dataset créé + images extraites).

        L'ingestion des .txt a déjà eu lieu à l'import du dataset : on vérifie
        seulement que les transcriptions sont disponibles avant de valider la tâche
        (décision réunion : "quand on lance un traitement paleography on vérifie
        bien que les transcriptions soient disponibles").
        """
        self.status = "PROCESSING RESULTS"
        self.result_full_path.mkdir(parents=True, exist_ok=True)

        output = (data or {}).get("output", {})

        # renseigne self.dataset.api_url à partir de output["dataset_url"]
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

        return super().on_task_success(data)