from django.db import transaction
from django.db.models import F
from interact.models import ChatSession


@transaction.atomic
def record_voice_usage(message):
    if not message.is_voice or message.audio_seconds <= 0:
        print(
            f"🎤 [VOICE] Skipping message.id={message.id}, audio_seconds={message.audio_seconds}, is_voice={message.is_voice}")
        return

    print(
        f"🎤 [VOICE] Recording audio usage: message.id={message.id}, session.id={message.session_id}, role={message.role}, audio_seconds={message.audio_seconds}")

    if message.role == message.USER:
        rows = ChatSession.objects.filter(id=message.session_id).update(
            user_audio_seconds=F('user_audio_seconds') + message.audio_seconds
        )
        print(f"🎤 [VOICE] User audio rows updated: {rows}")
        session = ChatSession.objects.get(id=message.session_id)
        print(
            f"🎤 [VOICE] New user_audio_seconds value: {session.user_audio_seconds}")
    else:
        rows = ChatSession.objects.filter(id=message.session_id).update(
            assistant_audio_seconds=F(
                'assistant_audio_seconds') + message.audio_seconds
        )
        print(f"🎤 [VOICE] Assistant audio rows updated: {rows}")
        session = ChatSession.objects.get(id=message.session_id)
        print(
            f"🎤 [VOICE] New assistant_audio_seconds value: {session.assistant_audio_seconds}")


def record_call_usage(call_session):
    if call_session.duration_seconds <= 0:
        return

    ChatSession.objects.filter(id=call_session.session_id).update(
        call_audio_seconds=F('call_audio_seconds') +
        call_session.duration_seconds
    )
