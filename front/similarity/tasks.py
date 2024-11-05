import dramatiq
import requests
from zipfile import ZipFile
import traceback

from .models import Similarity

"""
All dramatiq tasks related to Similarity retrieval
"""


@dramatiq.actor
def collect_results(experiment_id: str, result_url: str):
    pass
