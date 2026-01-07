import io
from mutagen.mp3 import MP3
from django.conf import settings
from elevenlabs.client import ElevenLabs


def tts_elevenlabs(content: str, *, model_id: str, voice_id: str):
    client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)

    if not content or not content.strip():
        return {'success': False, 'error': 'Empty text provided'}

    try:
        # Convert returns an iterator of audio chunks(bytes), not a complete file
        audio_stream = client.text_to_speech.convert(
            text=content,
            voice_id=voice_id,
            model_id=model_id,
            output_format='mp3_44100_128',
        )

        # Collect these chunks into BytesIO, building the full mp3 file in memory
        buf = io.BytesIO()
        for chunk in audio_stream:
            buf.write(chunk)
        audio_bytes = buf.getvalue()

        # Compute duration
        audio_file = MP3(io.BytesIO(audio_bytes))
        duration_seconds = round(audio_file.info.length)

        return {'success': True, 'audio_bytes': audio_bytes,
                'audio_seconds': duration_seconds, 'error': None}

    except Exception as e:
        return {'success': False, 'audio_bytes': None, 'audio_seconds': 0,
                'error': f'[TTS ERROR] {str(e)}'}
