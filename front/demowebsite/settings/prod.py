from .base import *

DEBUG = False
SECRET_KEY = ENV("SECRET_KEY")
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.postgresql_psycopg2",
        'NAME': ENV("DB_NAME"),
        'USER': ENV("DB_USER"),
        'PASSWORD': ENV("DB_PASSWORD"),
        'HOST': ENV("DB_HOST"),
        'PORT': ENV("DB_PORT"),
    }
}