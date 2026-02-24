from django.conf import settings
from django.core.cache import cache
from django.db.models.signals import post_save
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
        realtime_model=AIModel.objects.get(
            name=settings.DEFAULT_REALTIME_STT_MODEL_NAME
        ),
        stream_model=AIModel.objects.get(
            name=settings.DEFAULT_STREAM_TTS_MDOEL_NAME
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
