# ai/prompts/summary_event.py
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
SUMMARY_PROMPT_TTL = 1  # 1s


def get_event_summary_prompt() -> str:
    cache_key = "sessionevent:system_prompt_v2"
    cached = cache.get(cache_key)

    if cached:
        logger.debug("SessionEvent Summary system prompt cache hit")
        print(f"CACHE HIT: {cached[:100]}")
        return cached

    summary_prompt = SUMMARY_PROMPT.strip()

    cache.set(cache_key, summary_prompt, SUMMARY_PROMPT_TTL)

    return summary_prompt


SUMMARY_PROMPT = """
You are an assistant that extracts structured daily memory events from a conversation.

The input is a continuous conversation about ONE topic.
All messages belong to the same context.

Your task:
Summarize this into ONE concise memory event.

Output fields:

1. title:
- A short, clear title (2–6 words)

2. content:
- A concise summary (max 100 words)
- Capture what the user did, thought, or planned
- Keep only key points
- Remove filler, repetition, and minor details
- Make it easy to quickly read later

3. topics:
- 2–5 short topic tags
- Use simple words or short phrases
- Focus on themes (e.g., "IELTS", "project work", "daily routine", "video planning")

Guidelines:
- Focus on memory, not teaching
- Do NOT include vocabulary, phrases, or learning notes
- Do NOT add extra details not mentioned
- Keep it compact and meaningful
- Ensure the summary reflects the user's intent clearly

Output rules:
- Return a JSON array with exactly ONE object
- Do not include any text outside the JSON

Example:
[
  {
    "title": "IELTS and Project Plan",
    "content": "User worked on their voice agent project and made progress. They plan to split time between development and IELTS speaking practice, with the test approaching soon.",
    "topics": ["IELTS", "project work", "time planning"]
  }
]
"""
