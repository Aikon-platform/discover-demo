from pathlib import Path
from environ import Env
from django.urls import reverse_lazy

# path to front/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

ENV = Env()
# Read environment variables from .env file
Env.read_env(env_file=f"{BASE_DIR}/.env")

# Application definition
DEMO_APPS = [
    "dticlustering",
    "similarity",
    "watermarks",
    "regions",
    "pipelines",
    "search",
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_dramatiq",
    "django.contrib.admin",
    "shared",
    "tasking",
    "datasets",
] + DEMO_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "demowebsite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "demowebsite.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = Path(ENV("MEDIA_ROOT", default=BASE_DIR / "media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_HOST = ENV.str("REDIS_HOST", "localhost")
REDIS_PORT = ENV.str("REDIS_PORT", "6379")

redis_prefix = "redis://"

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq.brokers.redis.RedisBroker",
    "OPTIONS": {
        "url": f"{redis_prefix}{REDIS_HOST}:{REDIS_PORT}/0",
        # "url": ENV(
        #     "REDIS_URL", default="redis:///2"
        # ),
    },
    "MIDDLEWARE": [],
}


MAX_UPLOAD_SIZE = ENV("MAX_UPLOAD_SIZE", default=250 * 1024 * 1024)  # 250MB
DATA_UPLOAD_MAX_MEMORY_SIZE = ENV(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", default=25 * 1024 * 1024
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
        },
        "django.request": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django.core.mail": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s - %(levelname)s] %(funcName)s \n%(message)s \n"
        },
    },
}

LOGOUT_REDIRECT_URL = reverse_lazy("home")
