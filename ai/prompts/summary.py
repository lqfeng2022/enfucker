# ai/prompts/summary.py
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
SUMMARY_PROMPT_TTL = 60 * 60 * 24  # 24h


def get_summary_prompt() -> str:
    cache_key = 'chatsession_summary:system_prompt'
    cached = cache.get(cache_key)
    if cached:
        logger.debug('Summary system prompt cache hit')
        return cached

    # Build prompt:
    # simple, short, and LLM-friendly
    summary_prompt = """
    Maintain a short, clean memory of the conversation for future use.

    Update the summary using new dialogue.

    Rules:
    - Max ~120 words
    - Focus on user traits, goals, preferences, key context
    - Keep only useful info for future conversation
    - Use simple English
    - Use light structure (short paragraphs or bullets)
    - Remove outdated or trivial details
    - No meta text (e.g. "summary")

    Goal:
    Help the next reply feel natural and continuous.
    """.strip()

    cache.set(cache_key, summary_prompt, SUMMARY_PROMPT_TTL)
    return summary_prompt
