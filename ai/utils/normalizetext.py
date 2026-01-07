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
