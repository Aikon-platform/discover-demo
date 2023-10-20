from . import config
import os

# CELERY PART
from celery import Celery

celery = Celery(
    "dtiworker",
    backend=config.CELERY_BROKER_URL,
    broker=config.CELERY_BROKER_URL
)

celery.autodiscover_tasks(["app.tasks"])