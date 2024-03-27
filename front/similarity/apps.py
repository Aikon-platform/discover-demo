from django.apps import AppConfig

"""
This App contains the models and views related to the DTI clustering
"""


class SimilarityConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "similarity"
