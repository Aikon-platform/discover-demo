from . import config
from flask import Flask

from celery import Celery

app = Flask(__name__)
app.config.from_object(config.FLASK_CONFIG)

celery = Celery(
    app.name,
    backend=config.CELERY_BROKER_URL,
    broker=config.CELERY_BROKER_URL
)

from .routes import *