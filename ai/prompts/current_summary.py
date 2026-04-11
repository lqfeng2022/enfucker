# ai/prompts/summary.py
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
SUMMARY_PROMPT_TTL = 60 * 60 * 24  # 24h


def get_current_summary_prompt() -> str:
    cache_key = 'chatsession_current_summary:system_prompt_v0.0'
    cached = cache.get(cache_key)
    if cached:
        logger.debug('Current Summary system prompt cache hit')
        return cached

    summary_prompt = SESSION_CURRENT_SUMMARY_PROMPT.strip()

    cache.set(cache_key, summary_prompt, SUMMARY_PROMPT_TTL)
    return summary_prompt


SESSION_CURRENT_SUMMARY_PROMPT = """
You are maintaining a short, rolling memory of the user's current state in a chat session.

Context:
- You are given an existing summary ("Existing summary") and new chat messages ("New messages").
- Focus primarily on the USER's messages.
- Assistant messages are only for context.

Your task:
- Update the summary to reflect the user's current goals, intentions, preferences, or problems.
- Keep only the most important and relevant information.
- Merge with the existing summary while removing outdated or redundant details.

Rules:
- Prioritize USER input over assistant responses.
- Do NOT include unnecessary conversation details.
- Do NOT repeat information.
- Do NOT include message formatting like [USER] or [ASSISTANT].
- Do NOT invent information.

Output:
- Return ONLY the updated summary as plain text.
- Maximum 50 words.
- Write as a compact, clear snapshot of the user's current state.
"""
