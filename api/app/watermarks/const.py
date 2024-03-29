from pathlib import Path
from ..config.base import ENV, BASE_DIR

DEMO_NAME = "watermarks"

# Path to DEMO_NAME/ folder
DEMO_DIR = BASE_DIR / "app" / DEMO_NAME

WATERMARKS_MODEL_FOLDER = Path(
    ENV("WATERMARKS_MODEL_FOLDER", default=f"{DEMO_DIR}/data/models")
)
