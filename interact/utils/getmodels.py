from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_product_model():
    try:
        return apps.get_model(settings.STORE_PRODUCT_MODEL)
    except (ValueError, LookupError) as e:
        raise ImproperlyConfigured(
            'STORE_PRODUCT_MODEL is not configured correctly.') from e


def get_default_host():
    """Return the default chat host defined in settings."""
    Host = get_host_model()
    default_host = getattr(settings, 'DEFAULT_HOST_SLUG', None)

    if default_host is None:
        return f'Default chat host {default_host} does not exist.'
    return Host.objects.get(slug=default_host)


def get_host_model():
    """Resolve Host model from settings."""
    try:
        return apps.get_model(settings.STORE_HOST_MODEL)
    except (ValueError, LookupError) as e:
        raise ImproperlyConfigured(
            'STORE_HOST_MODEL is not configured correctly.') from e


def get_credit_account_model():
    try:
        return apps.get_model(settings.BILLING_CREDITACCOUNT_MODEL)
    except (ValueError, LookupError) as e:
        raise ImproperlyConfigured(
            'BILLING_CREDITACCOUNT_MODEL is not configured correctly.') from e
