import re


def normalize_text(text):
    """Normalize newlines and trim whitespace.
    """
    if not text:
        return ''

    # Normalize line breaks
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Strip each line
    lines = [line.rstrip() for line in text.split('\n')]
    cleaned = '\n'.join(lines)

    return cleaned


def format_text(text: str) -> str:
    """Format LLM output for chat-style display.
    """
    if not text:
        return ''

    text = normalize_text(text)

    # Remove markdown emphasis
    text = text.replace('*', '')

    # Collapse multiple newlines → max 1
    text = re.sub(r'\n+', '\n', text)

    # Convert newlines to space (chat style)
    text = text.replace('\n', ' ')

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
