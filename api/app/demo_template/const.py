from pathlib import Path
from ..config.base import ENV, BASE_DIR

DEMO_NAME = "template"

# Path to DEMO_NAME/ folder
DEMO_DIR = BASE_DIR / "app" / DEMO_NAME

DEMO_DATA_FOLDER = Path(ENV("API_DATA_FOLDER", default=f"{DEMO_DIR}/data")) / DEMO_NAME
