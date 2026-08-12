from urllib.parse import urlparse
from environ import Env

from .base import *

DEBUG = False
SECRET_KEY = ENV("SECRET_KEY")

ADMIN_EMAIL = ENV("ADMIN_EMAIL")
ADMINS = [(ENV("POSTGRES_USER"), ADMIN_EMAIL)]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": ENV.str("POSTGRES_DB", default="demowebsite"),
        "USER": ENV.str("POSTGRES_USER", default="demowebsite"),
        "PASSWORD": ENV.str("POSTGRES_PASSWORD"),
        "HOST": ENV.str("DB_HOST", default="db"),
        "PORT": ENV.str("DB_PORT", default="5432"),
    }
}

API_URL = ENV("PROD_API_URL")
BASE_URL = ENV("PROD_URL", default="")
DOMAIN_NAME = urlparse(BASE_URL).netloc

if ENV.bool("IS_API_ON_SAME_SERVER", default=False):
    DOCKER_PORT = ENV.int("DJANGO_PORT", 8000)
    INTERNAL_URL = f"http://web:{DOCKER_PORT}"
else:
    INTERNAL_URL = BASE_URL

hosts = ENV.list("ALLOWED_HOSTS", default=[]) + [DOMAIN_NAME, "localhost"]
hosts += ["web"]  # for docker nginx service
https_hosts = [f"https://{host}" for host in hosts]
wildcard_hosts = [f"https://*.{host}" for host in hosts if "." in host]

ALLOWED_HOSTS = hosts + https_hosts + wildcard_hosts
CSRF_TRUSTED_ORIGINS = https_hosts + wildcard_hosts

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = ENV("EMAIL_HOST", default="localhost")
EMAIL_PORT = ENV(
    "EMAIL_PORT", default=587
)  # 25 for unencrypted, 587 for TLS, 465 for SSL
EMAIL_USE_TLS = True if EMAIL_PORT == 587 else False
EMAIL_USE_SSL = True if EMAIL_PORT == 465 else False
EMAIL_HOST_USER = ENV("EMAIL_HOST_USER", default=ADMIN_EMAIL)
EMAIL_HOST_PASSWORD = ENV("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = ENV("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)
SERVER_EMAIL = ENV("SERVER_EMAIL", default=EMAIL_HOST_USER)
