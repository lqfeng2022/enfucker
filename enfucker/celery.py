import os
from celery import Celery


# setting this MODULE environment variable to enfucker.settings.dev
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'enfucker.settings.dev')

# create a celery instance
celery = Celery('enfucker')

# then specify where celery can find configuration variables
celery.config_from_object('django.conf:settings', namespace='CELERY')
celery.autodiscover_tasks()
