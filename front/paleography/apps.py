from django.apps import AppConfig

"""
Module Paleography (D1) : upload d'un dataset d'images de lignes accompagnées de
leurs transcriptions (.txt homonymes). Ne lance aucun traitement — le "start" ne
fait que charger le dataset, qui est alors typé "dataset à transcription".
"""


class PaleographyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "paleography"
