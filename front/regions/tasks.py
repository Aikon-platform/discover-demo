import dramatiq
import requests
from zipfile import ZipFile
import traceback

from .models import Regions

"""
All dramatiq tasks related to images regions extraction
"""


@dramatiq.actor
def collect_results(experiment_id: str, result_url: str):
    pass
