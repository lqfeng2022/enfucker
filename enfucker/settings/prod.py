import os
import dj_database_url
from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

DATABASES = {
    'default': dj_database_url.config()
}

DEEPSEEK_BASE_URL = 'https://api.deepseek.com'

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')


# Specify the server and server can run this application
# It’s only required if debug turned off
ALLOWED_HOSTS = [
    'clipwords.me',
    'www.clipwords.me',
]

# get the cookie from the front-end webss
SESSION_COOKIE_DOMAIN = '.clipwords.me'
CSRF_COOKIE_DOMAIN = '.clipwords.me'

# auth
AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = 'None'
AUTH_COOKIE_DOMAIN = '.clipwords.me'
