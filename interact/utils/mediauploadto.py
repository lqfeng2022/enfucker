import os
import uuid


def chat_audio_upload_to(instance, filename):
    """Upload to 'interact/audio/<instance.role>/<filename>'."""
    ext = os.path.splitext(filename)[1] or '.mp3'
    filename = f'{uuid.uuid4().hex}{ext}'

    return f'interact/audio/{instance.role}/{filename}'


def speaking_audio_upload_to(filename):
    """Upload to 'interact/audio/speaking/<filename>'."""
    ext = os.path.splitext(filename)[1] or '.mp3'
    filename = f'{uuid.uuid4().hex}{ext}'

    return f'interact/audio/speaking/{filename}'
