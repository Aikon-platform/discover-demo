from .base import *

DEBUG = True
SECRET_KEY = 'django-insecure-b(q90mzs928i@!2y-_=duur@tg=&=^6$l$3@!=4!%y)p91s=(2'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DTI_API_URL = 'http://localhost:5000'
BASE_URL = 'http://localhost:8000'

MEDIA_ROOT = Path(ENV("MEDIA_ROOT", default=BASE_DIR / "media"))