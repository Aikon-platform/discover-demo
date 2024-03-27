from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-b(q90mzs928i@!2y-_=duur@tg=&=^6$l$3@!=4!%y)p91s=(2"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

DTI_API_URL = f'http://localhost:{ENV("API_DEV_PORT")}'
BASE_URL = "http://localhost:8000"