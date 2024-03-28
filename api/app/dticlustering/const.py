from environ import Env
from pathlib import Path

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
DEMO_DIR = Path(__file__).resolve().parent.parent / DEMO_NAME

ENV = Env()
Env.read_env(env_file=f"{DEMO_DIR}/.env")

DTI_DATA_FOLDER = Path(ENV("DTI_DATA_FOLDER", default=f"{DEMO_DIR}/data"))
DTI_RESULTS_PATH = DTI_DATA_FOLDER / "results"
