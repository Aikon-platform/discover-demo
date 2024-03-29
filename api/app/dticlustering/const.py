from pathlib import Path
from ..config.base import ENV, BASE_DIR

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

DTI_DATA_FOLDER = Path(ENV("API_DATA_FOLDER", default=f"{DEMO_DIR}/data")) / DEMO_NAME
DTI_XACCEL_PREFIX = Path(ENV("DTI_XACCEL_PREFIX", default="/media/dti-results"))
DTI_RESULTS_PATH = DTI_DATA_FOLDER / "results"
