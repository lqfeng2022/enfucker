import os
import dj_database_url
from .common import *


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

# Specify the server and server can run this application
# It’s only required if debug turned off
ALLOWED_HOSTS = [
    'clipwords.me',
    'www.clipwords.me',
]

DATABASES = {
    'default': dj_database_url.config()
}
