from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile


@receiver(post_save, sender=User)
def create_profile_for_new_user(sender, **kwargs):
    if kwargs['created']:
        Profile.objects.create(user=kwargs['instance'])

# Work flow:
#  as we get a signal from a sender model that a new model instance created,
#  then we can do something here..

# 'post_save': a Django signal that gets triggered after a model’s save() method completes.
# 'sender': the model class
# 'created': a boolean — True if a new object was created, False if it was just updated
# 'instance': the model instance that was just saved
# **kwargs: extra context (e.g., update_fields, raw)
