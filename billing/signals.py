from django.conf import settings
from django.apps import apps
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CreditAccount

User = apps.get_model(settings.AUTH_USER_MODEL)


@receiver(post_save, sender=User)
def create_credit_account_for_new_user(sender, **kwargs):
    if kwargs['created']:
        CreditAccount.objects.create(user=kwargs['instance'])
