import os
from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver
from ai.utils.getmodels import get_host_model
from .models import HostProfile, BasePrompt, PersonaPrompt, AIModel, Voice

Host = get_host_model()


# When the prompt changes, flush only this prompt.
@receiver(post_save, sender=BasePrompt)
def invalidate_prompt_cache(sender, instance, **kwargs):
    cache.delete(f'prompt:db:{instance.slug}')
    cache.clear()  # optional if you version keys


def create_default_host_profile(host):
    HostProfile.objects.create(
        host=host,
        chat_model=AIModel.objects.get(
            name=settings.DEFAULT_CHAT_MODEL_NAME
        ),
        stt_model=AIModel.objects.get(
            name=settings.DEFAULT_STT_MODEL_NAME
        ),
        tts_model=AIModel.objects.get(
            name=settings.DEFAULT_TTS_MODEL_NAME
        ),
        base_prompt=BasePrompt.objects.get(
            slug=settings.DEFAULT_BASE_PROMPT_SLUG
        ),
        persona_prompt=PersonaPrompt.objects.get(
            slug=settings.DEFAULT_PERSONA_PROMPT_SLUG
        ),
        voice=Voice.objects.get(slug=settings.DEFAULT_VOICE_SLUG),
    )


@receiver(post_save, sender=Host)
def create_profile_for_new_host(sender, **kwargs):
    if kwargs['created']:
        create_default_host_profile(host=kwargs['instance'])


# Clean unused video files via signals
def delete_file_if_changed(old_file_field, new_file_field):
    if not (old_file_field or old_file_field.name):
        return
    elif old_file_field.name != new_file_field.name:
        if os.path.isfile(old_file_field.path):
            os.remove(old_file_field.path)


# Clean unused host images via signals
@receiver(post_delete, sender=HostProfile)
def cleanup_expimage_on_delete(sender, instance, **kwargs):
    if not instance.pk:
        return  # New object, no old file

    try:
        old_file = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    delete_file_if_changed(old_file.portrait, instance.portrait)
    delete_file_if_changed(old_file.cover, instance.cover)


@receiver(pre_save, sender=HostProfile)
def cleanup_expimage_on_replace(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_file = HostProfile.objects.get(pk=instance.pk)
    except HostProfile.DoesNotExist:
        return

    if old_file.portrait != instance.portrait:
        delete_file_if_changed(old_file.portrait, instance.portrait)

    if old_file.cover != instance.cover:
        delete_file_if_changed(old_file.cover, instance.cover)
