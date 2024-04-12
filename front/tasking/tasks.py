import dramatiq
import requests
from zipfile import ZipFile
import traceback


@dramatiq.actor
def test():
    """
    Test task to check if the dramatiq worker is running
    """
    print("test")
    return "test"
