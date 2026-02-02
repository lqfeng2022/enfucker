from django.conf import settings
from ai.models import AIModel, HostProfile, Voice
from ai.contracts import CHAT, STT, TTS, ENHANCE, SUMMARY, REALTIME, STREAM


def get_default_stt_model():
    return AIModel.objects.get(name='scribe_v1')


def get_default_tts_model():
    return AIModel.objects.get(name='eleven_v3')


def get_default_realtime_model():
    return AIModel.objects.get(name='scribe_v2_realtime')


def get_default_stream_model():
    return AIModel.objects.get(name='eleven_multilingual_v2')


def get_default_tts_voice():
    default_tts_voice = getattr(settings, 'DEFAULT_VOICE_SLUG', None)
    return Voice.objects.get(slug=default_tts_voice)


def get_internal_model(*, usecase: str):
    if usecase in (SUMMARY, ENHANCE):
        return AIModel.objects.get(name='deepseek-chat')
    return None


def resolve_model(*, profile: HostProfile, usecase: str):
    if usecase == CHAT:
        return profile.chat_model

    if usecase == TTS:
        return profile.tts_model or get_default_tts_model()

    if usecase == STT:
        return profile.stt_model or get_default_stt_model()

    if usecase == REALTIME:
        return profile.realtime_model or get_default_realtime_model()

    if usecase == STREAM:
        return profile.stream_model or get_default_stream_model()

    # Internal usecases
    if usecase in (SUMMARY, ENHANCE):
        return get_internal_model(usecase=usecase) or profile.chat_model

    raise ValueError(f'Unsupported usecase: {usecase}')
