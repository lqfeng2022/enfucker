from decimal import Decimal
from django.core.files.base import ContentFile
from ai.engines.tts import tts_elevenlabs
from ai.services.get_modelprovider import get_tts_model_provider, resolve_tts_voice
from ai.services.get_aimodel import resolve_model
from ai.contracts import TTS
from interact.utils.recorder import record_usage
from interact.utils.credits import require_credits
import logging

logger = logging.getLogger(__name__)


# Optional TTS Audio Generation
@require_credits(min_credits=100)
def assistant_tts_audio(*, message, is_voice=True):
    """Convert text (enhanced or plain) to audio.
    Safe failure: continues even if TTS fails. Returns saved audio or None.
    """
    if not is_voice:
        return None

    tts_text = (message.enhanced_content or message.content or '').strip()
    if not tts_text:
        return None

    profile = message.session.host.host_profile
    model = resolve_model(profile=profile, usecase=TTS)
    tts_model = get_tts_model_provider(model=model)
    tts_voice = resolve_tts_voice(voice=profile.voice)

    try:
        tts_result = tts_elevenlabs(
            tts_text,
            model_id=tts_model.model.name,
            voice_id=tts_voice
        )

        if not tts_result['success']:
            logger.error('TTS generation failed', extra={
                'assistant_msg_id': message.id,
                'voice': tts_voice,
                'error': tts_result.get('error')
            })
            return None

        # Save audio
        # Filename passed here ('tts.mp3') is overridden by ChatMessage.audio.upload_to
        audio_file = ContentFile(tts_result['audio_bytes'], name='tts.mp3')
        message.audio.save('tts.mp3', audio_file, save=False)

        message.audio_seconds = tts_result['audio_seconds']
        message.is_voice = is_voice
        message.save(
            update_fields=['audio', 'audio_seconds', 'is_voice']
        )

        # Record TTS usage
        if message.audio_seconds > 0:
            record_usage(
                message=message,
                model=tts_model,
                units=Decimal(len(tts_text)),
                projection_audio=True,
            )

        return message.audio

    except Exception as e:
        logger.exception('TTS generation failed', extra={
            'assistant_msg_id': message.id,
            'voice': tts_voice,
        })
        return None
