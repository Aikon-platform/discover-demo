import dramatiq
import requests
from zipfile import ZipFile
import traceback

from .models import Similarity

"""
All dramatiq tasks related to the DTI clustering
"""


@dramatiq.actor
def collect_results(dticlustering_id: str, result_url: str):
    pass
