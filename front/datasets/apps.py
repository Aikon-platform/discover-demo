import os

from django.apps import AppConfig

from demowebsite import settings

"""
This app contains the models and views related to the datasets,
that may be shared in future applications independent from the DTI clustering
"""


class DatasetsConfig(AppConfig):
    def ready(self):
        datasets_dir = os.path.join(settings.MEDIA_ROOT, "datasets")
        documents_dir = os.path.join(settings.MEDIA_ROOT, "documents")
        os.makedirs(datasets_dir, exist_ok=True)
        os.makedirs(documents_dir, exist_ok=True)

    default_auto_field = "django.db.models.BigAutoField"
    name = "datasets"
