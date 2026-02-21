from django.db.models import F
from interact.models import ChatSession


def record_voice_usage(message):
    if not message.is_voice or message.audio_seconds <= 0:
        return

    if message.role == message.USER:
        ChatSession.objects.filter(id=message.session_id).update(
            user_audio_seconds=F('user_audio_seconds') + message.audio_seconds
        )
    else:
        ChatSession.objects.filter(id=message.session_id).update(
            assistant_audio_seconds=F(
                'assistant_audio_seconds') + message.audio_seconds
        )


def record_call_usage(call_session):
    if call_session.duration_seconds <= 0:
        return

    ChatSession.objects.filter(id=call_session.session_id).update(
        call_audio_seconds=F('call_audio_seconds') +
        call_session.duration_seconds
    )
