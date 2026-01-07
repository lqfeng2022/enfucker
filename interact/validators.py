# Enforce 'text XOR audio' validation (VERY IMPORTANT)
def validate_text_audio_input(*, content=None, audio=None):
    """Enforce text XOR audio invariant. Raises ValueError (domain-level).
    """
    content = (content or '').strip()

    if not content and not audio:
        raise ValueError('Either content or audio must be provided.')

    if content and audio:
        raise ValueError('Provide either content or audio, not both.')

    return {
        'content': content,
        'audio': audio,
    }
