import os
from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'enfucker_db'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'USER': os.environ.get('DB_USER', 'kouji'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}


DEEPSEEK_BASE_URL = 'https://api.deepseek.com'

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')


# test purpose, delete it later
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
]
