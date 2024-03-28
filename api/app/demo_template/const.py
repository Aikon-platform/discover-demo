from environ import Env
from pathlib import Path

DEMO_NAME = "shared"

# Path to DEMO_NAME/ folder
DEMO_DIR = Path(__file__).resolve().parent.parent / DEMO_NAME

ENV = Env()
Env.read_env(env_file=f"{DEMO_DIR}/.env")
