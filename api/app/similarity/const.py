from environ import Env
from pathlib import Path
from ..shared.utils.fileutils import create_dirs_if_not, create_file_if_not
from ..config.base import ENV, BASE_DIR


DEMO_NAME = "similarity"

# Path to similarity/ folder
DEMO_DIR = BASE_DIR / "app" / DEMO_NAME
LIB_PATH = DEMO_DIR / "lib"

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

MAX_SIZE = 244
MAX_RES = 500

FEAT_NET = "moco_v2_800ep_pretrain"
FEAT_SET = "imagenet"
FEAT_LAYER = "conv4"
COS_TOPK = 20
SEG_TOPK = 10
SEG_STRIDE = 16
FINAL_TOPK = 25
