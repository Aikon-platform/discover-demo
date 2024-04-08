from pathlib import Path
from ..shared.utils.fileutils import create_dirs_if_not, create_file_if_not
from ..config.base import ENV, BASE_DIR


DEMO_NAME = "similarity"

# Path to similarity/ folder
DEMO_DIR = BASE_DIR / "app" / DEMO_NAME
LIB_PATH = DEMO_DIR / "lib"

SIM_QUEUE = "queue2"  # see docker-confs/supervisord.conf

SIM_DATA_FOLDER = Path(ENV("API_DATA_FOLDER", default=f"{DEMO_DIR}/data")) / DEMO_NAME
SIM_XACCEL_PREFIX = Path(ENV("SIM_XACCEL_PREFIX", default="/media/similarity-results"))
SIM_RESULTS_PATH = SIM_DATA_FOLDER / "results"

IMG_PATH = SIM_DATA_FOLDER / "documents"
MODEL_PATH = SIM_DATA_FOLDER / "models"
SCORES_PATH = SIM_RESULTS_PATH
FEATS_PATH = SIM_DATA_FOLDER / "feats"

create_dirs_if_not([IMG_PATH, MODEL_PATH, SCORES_PATH, FEATS_PATH])

IMG_LOG = Path(f"{DEMO_DIR}/img.log")

create_file_if_not(IMG_LOG)
