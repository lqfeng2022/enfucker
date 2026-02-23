from decimal import Decimal
from ai.engines.stt import stt_elevenlabs
from ai.services.get_modelprovider import get_stt_model_provider
from ai.services.get_aimodel import resolve_model
from ai.contracts import STT
from interact.models import ChatMessage
from interact.utils.recorder import record_usage
from interact.validators import validate_text_audio_input
from interact.utils.credits import require_credits
import logging

logger = logging.getLogger(__name__)


@require_credits(min_credits=10)
def create_user_message(*, session, content=None, audio=None):
    """Create a USER message.
    Invariants:
    - text XOR audio
    - content is always normalized
    """
    validated = validate_text_audio_input(content=content, audio=audio)

    user_msg = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.USER,
        content=validated['content'],
        audio=validated['audio'],
        is_voice=False,
    )

    if validated['audio']:
        process_stt_for_message(user_msg)

    return user_msg


def process_stt_for_message(message: ChatMessage):
    """Convert audio to text, update the message content, record usage."""
    model = resolve_model(profile=message.session.host.host_profile,
                          usecase=STT)
    stt_model = get_stt_model_provider(model=model)
    stt_result = stt_elevenlabs(message.audio, model_id=stt_model.model.name)

    if not stt_result.get('success'):
        logger.warning('STT failed', extra={
            'message_id': message.id,
            'session_id': message.session.id,
            'model': stt_model.model.name,
            'error': stt_result.get('error')
        })

        message.content = ''
        message.save(update_fields=['content'])
        return

    # Update message
    message.content = stt_result.get('text', '')
    message.audio_seconds = stt_result.get('seconds', 0)
    message.is_voice = True
    message.save(update_fields=['content', 'audio_seconds', 'is_voice'])

    # Record usage
    if message.audio_seconds > 0:
        record_usage(
            message=message,
            model=stt_model,
            units=Decimal(message.audio_seconds),
            projection_audio=True
        )
