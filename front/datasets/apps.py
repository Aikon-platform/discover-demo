from django.apps import AppConfig


"""
This app contains the models and views related to the datasets,
that may be shared in future applications independent from the DTI clustering
"""


class DatasetsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datasets"
