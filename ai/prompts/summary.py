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

    # Build prompt
    summary_prompt = (
        'You maintain an ongoing summary of a conversation.\n'
        'Update the existing summary using the new dialogue below.\n'
        'Preserve important facts, decisions, user preferences, goals, and tone.\n'
        'Do NOT repeat trivial chat.\n'
        'Do NOT remove previously relevant information unless it is contradicted.'
    )

    cache.set(cache_key, summary_prompt, SUMMARY_PROMPT_TTL)
    return summary_prompt
