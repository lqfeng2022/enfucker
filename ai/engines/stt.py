from io import BytesIO
from elevenlabs.client import ElevenLabs
from django.conf import settings


def stt_elevenlabs(audio_file, *, model_id: str):
    """Convert a Django FileField audio file to text using ElevenLabs STT.
    Returns '' if audio is missing or conversion fails.
    """
    elevenlabs = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    if not audio_file:
        return {'success': False, 'error': 'No audio provided'}

    try:
        # Read bytes (storage-agnostic)
        with audio_file.open('rb') as f:
            audio_bytes = f.read()

        # ElevenLabs STT
        transcription = elevenlabs.speech_to_text.convert(
            file=BytesIO(audio_bytes),
            model_id=model_id,
            tag_audio_events=True,
            language_code=None,
            diarize=True,
        )

        text = getattr(transcription, 'text', None)
        if not text or not text.strip():
            return {'success': False, 'error': 'Empty transcription'}

        # Duration from STT words (WebM-safe)
        words = getattr(transcription, 'words', [])
        audio_seconds = round(words[-1].end) if words else 0

        return {
            'success': True,
            'text': text.strip(),
            'seconds': audio_seconds,
            'model_id': model_id,
        }

    except Exception as e:
        return {'success': False, 'error': f'[STT ERROR] {str(e)}'}
