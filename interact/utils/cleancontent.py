import re


def clean_content(raw: str) -> str:
    """Compress whitespace inside assistant responses."""
    return re.sub(r'\s+', ' ', raw.strip())
