from flask import Flask
from celery import Celery

from . import config

app = Flask(__name__)
app.config.from_object(config.FLASK_CONFIG)

celery = Celery(
    app.import_name,
    backend=config.CELERY_BROKER_URL,
    broker=config.CELERY_BROKER_URL
)
celery.conf.update(app.config)

from .routes import *