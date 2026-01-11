import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# `.parent.parent` -> `.parent.parent.parent`
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Load .env file if it exists
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'corsheaders',
    'rest_framework',
    'djoser',
    'debug_toolbar',
    'core',
    'store',
    'interact',
    'ai',
    'billing',
]


MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]


# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'https://clipenglish.netlify.app',
    'https://app.clipwords.me',
]

# Cookies
SESSION_COOKIE_SAMESITE = 'None'  # or 'None' + Secure if cross-origin
SESSION_COOKIE_SECURE = True    # only True if using HTTPS

SESSION_ENGINE = 'django.contrib.sessions.backends.db'  # or cache/db/etc


ROOT_URLCONF = 'enfucker.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'enfucker.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.CookieJWTAuthentication',
        # Check the cookie first, then Authorization header
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    # 'minutes=5' by default
    'ACCESS_TOKEN_LIFETIME': timedelta(days=5),
}


# core app
AUTH_USER_MODEL = 'core.User'

# store app
STORE_HOST_MODEL = 'store.Host'
STORE_LANGUAGE_MODEL = 'store.Language'
STORE_CITY_MODEL = 'store.City'
STORE_PRODUCT_MODEL = 'store.Product'
DEFAULT_HOST_SLUG = 'lucy'

# billing app
BILLING_PAYMENT_MODEL = 'billing.Payment'
BILLING_CREDITACCOUNT_MODEL = 'billing.CreditAccount'

# ai app
AI_MODELPROVIDER_MODEL = 'ai.ModelProvider'

DEFAULT_CHAT_MODEL_NAME = 'deepseek-chat'
DEFAULT_STT_MODEL_NAME = 'scribe_v1'
DEFAULT_TTS_MODEL_NAME = 'eleven_v3'

DEFAULT_BASE_PROMPT_SLUG = 'language-teacher'
DEFAULT_PERSONA_PROMPT_SLUG = 'lucy'
DEFAULT_VOICE_SLUG = 'samara'


DJOSER = {'SERIALIZERS': {
    'user_create': 'core.serializers.UserCreateSerializer',
    'current_user': 'core.serializers.UserSerializer',
}}


# Loging configuring
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'general.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
        }
    },
    'formatters': {
        'verbose': {
            'format': '{asctime} ({levelname}) - {name} - {message}',
            'style': '{',
        }
    },
}


# Redis url
# `/1`: the db name, it could be 2/3.., `1` by convention
CELERY_BROKER_URL = 'redis://localhost:6379/1'


# Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # Or LocMemCache
        'LOCATION': 'redis://127.0.0.1:6379/2',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient'
        },
        'TIMEOUT': None,  # optional
    }
}
