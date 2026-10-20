from urllib.parse import urlparse
from environ import Env

from .base import *

DEBUG = False
SECRET_KEY = ENV("SECRET_KEY")

ADMIN_EMAIL = ENV("ADMIN_EMAIL")
ADMINS = [(ENV("POSTGRES_USER"), ADMIN_EMAIL)]

API_URL = ENV("PROD_API_URL")
BASE_URL = ENV("PROD_URL", default="")

if ENV.bool("IS_API_ON_SAME_SERVER", default=False):
    DOCKER_PORT = ENV.int("DJANGO_PORT", 8000)
    INTERNAL_URL = f"http://web:{DOCKER_PORT}"
else:
    INTERNAL_URL = BASE_URL

# URL for the API to send HTTP requests to the Django app
# if the API is dockerized with the frontend, container name is used;
# otherwise, a localhost URL or actual URL will be used
APP_URL_FROM_API = ENV.str("APP_URL_FROM_API", default=BASE_URL)

DOMAIN_NAME = urlparse(BASE_URL).netloc

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
