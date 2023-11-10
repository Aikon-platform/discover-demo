from django.apps import AppConfig

"""
This app is used for shared functionality between the frontend coponents
"""

class SharedConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shared'
