from ai.contracts import CHAT, STT, STREAM, TTS, REALTIME, ENHANCE, SUMMARY
from ai.models import ModelProvider, Voice
from ai.services.get_aimodel import get_default_tts_voice


def get_chat_model_provider(*, model):
    input_cache_provider = ModelProvider.objects.get(
        model=model,
        usecase=CHAT,
        step=ModelProvider.CACHED_INPUT,
    )

    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=CHAT,
        step=ModelProvider.INPUT,
    )

    output_provider = ModelProvider.objects.get(
        model=model,
        usecase=CHAT,
        step=ModelProvider.OUTPUT,
    )

    return input_cache_provider, input_provider, output_provider


def get_stt_realtime_model_provider(*, model):
    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=REALTIME,
        step=ModelProvider.INPUT,
    )

    return input_provider


def get_stt_model_provider(*, model):
    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=STT,
        step=ModelProvider.INPUT,
    )

    return input_provider


def get_tts_stream_model_provider(*, model):
    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=STREAM,
        step=ModelProvider.INPUT,
    )

    return input_provider


def get_tts_model_provider(*, model):
    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=TTS,
        step=ModelProvider.INPUT,
    )

    return input_provider


def resolve_tts_voice(*, voice: Voice):
    """Resolve ElevenLabs voice_id."""
    if voice and voice.is_active and voice.voice_id:
        return voice.voice_id

    default_voice = get_default_tts_voice()

    return default_voice.voice_id


def get_enhancement_model(*, model):
    input_cache_provider = ModelProvider.objects.get(
        model=model,
        usecase=ENHANCE,
        step=ModelProvider.CACHED_INPUT,
    )

    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=ENHANCE,
        step=ModelProvider.INPUT,
    )

    output_provider = ModelProvider.objects.get(
        model=model,
        usecase=ENHANCE,
        step=ModelProvider.OUTPUT,
    )

    return input_cache_provider, input_provider, output_provider


def get_summary_model(*, model):
    input_cache_provider = ModelProvider.objects.get(
        model=model,
        usecase=SUMMARY,
        step=ModelProvider.CACHED_INPUT,
    )

    input_provider = ModelProvider.objects.get(
        model=model,
        usecase=SUMMARY,
        step=ModelProvider.INPUT,
    )

    output_provider = ModelProvider.objects.get(
        model=model,
        usecase=SUMMARY,
        step=ModelProvider.OUTPUT,
    )

    return input_cache_provider, input_provider, output_provider
