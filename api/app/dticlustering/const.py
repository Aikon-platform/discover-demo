from pathlib import Path
from ..config.base import ENV, BASE_DIR, API_DATA_FOLDER, XACCEL_PREFIX

# TODO add results dir, run dir etc.
from .lib.src.utils.path import (
    DATASETS_PATH,
    RUNS_PATH,
    RESULTS_PATH,
    CONFIGS_PATH,
    RUNS_PATH,
)

DEMO_NAME = "dticlustering"

# Path to DEMO_NAME/ folder
DEMO_DIR = BASE_DIR / "app" / DEMO_NAME

DTI_DATA_FOLDER = API_DATA_FOLDER / DEMO_NAME
DTI_XACCEL_PREFIX = f"{XACCEL_PREFIX}/{DEMO_NAME}"
DTI_RESULTS_PATH = DTI_DATA_FOLDER / "results"
DTI_QUEUE = "queue0"  # see docker-confs/supervisord.conf