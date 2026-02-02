# interact/usecases/text_segmentation.py
import re


MIN_DELTA_CHARS = 5


# ignore partials shorter than 5 characters
def delta_length_ok(text: str, committed_prefix: str, min_chars: int = MIN_DELTA_CHARS) -> bool:
    delta_text = text[len(committed_prefix):].strip()
    return len(delta_text) >= min_chars


def split_into_sentences(text: str) -> list[str]:
    if not text.strip():
        return []  # skip the empty string

    # Regex pattern for sentence-ending punctuation (English + CJK)
    pattern = r"[^。！？.!?]+[。！？.!?]?"
    sentences = re.findall(pattern, text)

    # Clean sentences
    return [s.strip() for s in sentences if s.strip()]


def get_new_sentences(full_text: str, committed_prefix: str) -> str:
    full_sents = split_into_sentences(full_text)
    committed_sents = split_into_sentences(committed_prefix)

    # nothing committed yet → everything is new
    if not committed_sents:
        return "".join(full_sents).strip()

    # --- 1. Try strict prefix alignment ---
    i = 0
    while (
        i < len(committed_sents)
        and i < len(full_sents)
        and committed_sents[i] == full_sents[i]
    ):
        i += 1

    # If we matched ALL committed sentences as a prefix,
    # then everything after is new
    if i == len(committed_sents):
        return "".join(full_sents[i:]).strip()

    # --- 2. Fallback: suffix by count ---
    delta = len(full_sents) - len(committed_sents)
    if delta > 0:
        return "".join(full_sents[-delta:]).strip()

    # --- 3. Otherwise, nothing confidently new ---
    return ""


def sanitize_stt_text(text: str) -> str:
    # Remove parenthetical meta speech
    text = re.sub(r"$begin:math:text$\[\^\)\]\*$end:math:text$", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def format_for_tts(text: str) -> str:
    # Remove stage directions: (laughs), (smiling), etc.
    text = re.sub(r"\([^)]*\)", "", text)

    # Remove markdown emphasis
    text = re.sub(r"[*_~`]", "", text)

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()
