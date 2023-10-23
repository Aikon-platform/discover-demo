from environ import Env
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV = Env()
Env.read_env(env_file=f"{BASE_DIR}/.env")

class FLASK_CONFIG():
    pass

BROKER_URL = "redis:///1"