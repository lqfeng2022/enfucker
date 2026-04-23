import re

EMOJI_PATTERN = r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]'
# \U0001F600-\U0001F64F - Emoticons (😀 to 🙏)
# \U0001F300-\U0001F5FF - Misc Symbols and Pictographs (🌀 to 🗿)
# \U0001F680-\U0001F6FF - Transport and Map (🚀 to 🛿)
# \U0001F1E0-\U0001F1FF - Regional Indicator Symbols (🇦 to 🇿, used for flags)


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

    # Remove emojis
    text = re.sub(EMOJI_PATTERN, '', text)

    # Remove all asterisks
    text = text.replace('*', '')

    # Use space instead of em-dash
    text = re.sub(r'\s*—\s*', ' ', text)

    # Collapse multiple newlines → max 1
    text = re.sub(r'\n+', '\n', text)

    # Convert newlines to space (chat style)
    text = text.replace('\n', ' ')

    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()
