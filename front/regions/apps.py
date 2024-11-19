from django.apps import AppConfig

"""
This App contains the models and views related to the Region extraction demo
"""


class RegionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "regions"
