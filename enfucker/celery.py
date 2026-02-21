import os
from celery import Celery
from dotenv import load_dotenv

# load .env explicitly
load_dotenv()

# DO NOT hardcode dev/prod here
# Let systemd or manage.py control it
# setdefault() only sets it if it is NOT already set.
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    os.getenv('DJANGO_SETTINGS_MODULE', 'enfucker.settings.dev')
)

# create a celery instance
celery = Celery('enfucker')

# then specify where celery can find configuration variables
celery.config_from_object('django.conf:settings', namespace='CELERY')
celery.autodiscover_tasks()
