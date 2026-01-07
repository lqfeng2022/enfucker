from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_host_model():
    """Resolve Host model from settings."""
    try:
        return apps.get_model(settings.STORE_HOST_MODEL)
    except (ValueError, LookupError) as e:
        raise ImproperlyConfigured(
            'STORE_HOST_MODEL is not configured correctly.') from e
