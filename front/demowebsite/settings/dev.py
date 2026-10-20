from urllib.parse import urlparse

from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-b(q90mzs928i@!2y-_=duur@tg=&=^6$l$3@!=4!%y)p91s=(2"

INTERNAL_IPS = [
    "127.0.0.1",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

API_URL = ENV("API_URL", default=f"http://localhost:{ENV('API_PORT', default=5000)}")
BASE_URL = f"http://localhost:{ENV('FRONT_PORT', default=8000)}"
INTERNAL_URL = BASE_URL

DOMAIN_NAME = urlparse(BASE_URL).netloc

hosts = ENV.list("ALLOWED_HOSTS", default=[]) + [DOMAIN_NAME, "localhost"]
hosts += ["web"]  # for docker nginx service
https_hosts = [f"https://{host}" for host in hosts]
wildcard_hosts = [f"https://*.{host}" for host in hosts if "." in host]

ALLOWED_HOSTS = hosts + https_hosts + wildcard_hosts
CSRF_TRUSTED_ORIGINS = https_hosts + wildcard_hosts

# URL for the API to send HTTP requests to the Django app
# if the API is dockerized with the frontend, container name is used;
# otherwise, a localhost URL or actual URL will be used
APP_URL_FROM_API = ENV.str("APP_URL_FROM_API", default=BASE_URL)

LOGIN_REQUIRED = True
