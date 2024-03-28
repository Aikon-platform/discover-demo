from pathlib import Path
from ..shared.const import ENV

# Path to api/ folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent

INSTALLED_APPS = ENV("INSTALLED_APPS").split(",")

for app in INSTALLED_APPS:
    # import .env variables for each installed app
    exec(f"from ..{app}.const import *")


class FLASK_CONFIG:
    pass


BROKER_URL = "redis:///1"
# BROKER_URL = f"redis://:{ENV('REDIS_PASSWORD')}@localhost:6379/1"

USE_NGINX_XACCEL = False
