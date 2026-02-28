def normalize_text(text):
    """Replace all CRLF and CR with LF and strip excessive blank lines."""
    if not text:
        return ''
    # Replace \r\n or \r with \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    # Remove multiple consecutive newlines
    lines = [line.rstrip() for line in text.split('\n')]
    cleaned = '\n'.join(lines)
    return cleaned


def format_text(text: str) -> str:
    """Apply common formatting to LLM output.

    Currently this does the same normalization as :func:`normalize_text` and
    additionally strips all asterisk characters used for markdown emphasis.
    We keep the transformation loose here so other usecases can build on it
    later (e.g. removing other markdown decorations).
    """
    if not text:
        return ''

    # normalize whitespace/newlines first
    formatted = normalize_text(text)
    # remove all "*" characters, which the LLM sometimes inserts for
    # emphasis (bold/italic).  Stripping them avoids unintended markup in
    # persisted messages and across the UI.
    return formatted.replace('*', '')
