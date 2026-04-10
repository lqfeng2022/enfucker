from django.db import transaction
from ai.engines.llm_chat import deepseek_engine
from ai.prompts.summary import get_summary_prompt
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.contracts import SUMMARY
from interact.utils.recorder import record_usage
from interact.models import ChatSession, SessionSummary
import json
import logging

logger = logging.getLogger(__name__)


def session_summary(*, session: ChatSession):
    """
    Generate or update a session-wide summary from all SessionEvent objects.
    Follows the same style as session_message_rewrite: debug prints, model resolve, token usage.
    """

    # Collect all events for the session ---
    events = list(
        session.events
        .order_by("created_at")
        .values("title", "content", "topics")
    )
    if not events:
        logger.info("No session events to summarize")
        return None

    # Build LLM messages ---
    system_prompt = get_summary_prompt()
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(events)}
    ]

    # Resolve model and call LLM ---
    model = resolve_model(profile=session.host.host_profile, usecase=SUMMARY)
    input_cache, input_model, output_model = get_summary_model(model=model)

    result = deepseek_engine(messages_payload, model=output_model.model.name)
    if not result.get("success", False):
        logger.error("Session summary generation failed")
        return None

    content = result.get("content", "").strip()
    if not content:
        logger.warning("Empty AI response for session summary")
        return None

    # Parse JSON output ---
    summary_data = _extract_json(content)
    if isinstance(summary_data, dict):
        content = summary_data.get("content", "")
        topics = summary_data.get("topics", [])
    else:
        logger.warning("Invalid JSON output from AI")
        content = ""
        topics = []

    # Save/update SessionSummary ---
    with transaction.atomic():
        summary, _ = SessionSummary.objects.update_or_create(
            session=session,
            defaults={"content": content, "topics": topics},
        )

    # Record token usage ---
    usage = result.get("usage", {}) or {}
    if usage.get("input_cached_tokens"):
        record_usage(session=session, model=input_cache,
                     units=usage.get("input_cached_tokens"))
    if usage.get("input_tokens"):
        record_usage(session=session, model=input_model,
                     units=usage["input_tokens"])
    if usage.get("output_tokens"):
        record_usage(session=session, model=output_model,
                     units=usage["output_tokens"])

    return summary


def _extract_json(content: str):
    """Extract JSON object from AI output, handles raw JSON or markdown blocks."""
    if not content:
        return {}

    content = content.strip()

    # handle markdown-style ```json ... ```
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode failed", extra={
                       "error": str(e), "content": content})
        return {}
