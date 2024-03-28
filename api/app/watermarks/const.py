from environ import Env
from pathlib import Path

DEMO_NAME = "watermarks"

# Path to DEMO_NAME/ folder
DEMO_DIR = Path(__file__).resolve().parent.parent / DEMO_NAME

ENV = Env()
Env.read_env(env_file=f"{DEMO_DIR}/.env")

WATERMARKS_MODEL_FOLDER = Path(
    ENV("WATERMARKS_MODEL_FOLDER", default=f"{DEMO_DIR}/data/models")
)
