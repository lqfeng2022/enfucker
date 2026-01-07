from ai.utils.normalizetext import normalize_text
from django.core.cache import cache
import logging

PROMPT_TTL = 60 * 60 * 24  # 24h
logger = logging.getLogger(__name__)


def build_elevenlabs_prompt(instructions: str | None):
    if not instructions:
        return ''

    # Instructions text is the cache boundary
    cache_key = f'prompt:enhancement:{hash(instructions)}'

    cached = cache.get(cache_key)
    if cached:
        logger.debug('Enhancement system prompt cache hit')
        return cached

    # Normalize and build prompt
    blocks = [
        '=== ENHANCEMENT INSTRUCTIONS ===',
        normalize_text(instructions),
    ]

    result = normalize_text(
        '\n\n'.join([b.strip() for b in blocks if b and b.strip()])
    )

    cache.set(cache_key, result, PROMPT_TTL)
    return result
