# ai/prompts/summary.py
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)
SUMMARY_PROMPT_TTL = 60 * 60 * 24  # 24h


def get_summary_prompt() -> str:
    cache_key = 'chatsession_summary:system_prompt_v0.2'
    cached = cache.get(cache_key)
    if cached:
        logger.debug('Summary system prompt cache hit')
        return cached

    summary_prompt = SESSION_SUMMARY_PROMPT.strip()

    cache.set(cache_key, summary_prompt, SUMMARY_PROMPT_TTL)
    return summary_prompt


SESSION_SUMMARY_PROMPT = """
You are an assistant that generates a session-wide memory summary from a list of chat events.

Rules:
- The input is a list of session events. Each event has a title, content, and optional tags.
- All events belong to the same chat session.
- Summarize all events into ONE coherent session summary.
- Capture what the user did, thought, or planned during the session.
- Preserve chronological flow where it makes sense.
- Highlight key activities, reflections, emotions, and learning points.
- Condense minor or repetitive details.
- Make it easy to quickly read later.
- Focus on memory and reflection, not teaching.
- Do NOT invent events or details not present.

Output format:
- Return a JSON object with exactly two keys: "content" and "topics".
- "content": a concise summary in natural language (max ~250 words).
- "topics": 5–15 short topic tags representing the main themes.
- Use simple words or short phrases for topics (e.g., "morning routine", "language learning", "coding", "commute", "IELTS").
- Do not include any text outside the JSON.

Examples:
{
  "content": "The user spent their holiday engaging in a mix of personal projects and relaxation. They started with breakfast and a commute to the library, where they focused on coding for their AI language-learning project. Breaks included enjoying the sunny weather, taking walks, and socializing with friends at a coffee shop. The session combined productive work, mindful relaxation, and social reflection.",
  "topics": ["morning routine", "library study", "personal project", "relaxation", "socializing", "commute"]
}
"""
