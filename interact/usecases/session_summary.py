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


# Public API
def session_summary(*, session: ChatSession):
    """
    Generate or update a session-wide summary from all SessionEvent objects.
    Follows the same style as session_message_rewrite: debug prints, model resolve, token usage.
    """
    # Collect all events for the session
    events = _get_events(session)
    if not events:
        return None

    # Build LLM messages using events
    messages = _build_llm_messages(events)

    # Call LLM to get a result
    result = _call_llm(session, messages)
    if not result:
        return None

    # Get a formated data from the result
    parsed = _parse_result(result)
    if not parsed:
        return None

    # Save the parsed data to DB then record the token usage
    summary = _save_summary(session, parsed)
    _record_usage(session, result)

    return summary


def _get_events(session):
    events = list(
        session.events
        .order_by("created_at")
        .values("title", "content", "topics")
    )

    if not events:
        logger.info(
            "No session events to summarize",
            extra={"session_id": session.id}
        )
        return []

    return events


def _build_llm_messages(events):
    system_prompt = get_summary_prompt()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(events)},
    ]


def _call_llm(session, messages):
    host_profile = session.host.host_profile
    model = resolve_model(profile=host_profile, usecase=SUMMARY)

    _, input_model, output_model = get_summary_model(model=model)

    deepseek_model = output_model.model.name
    result = deepseek_engine(messages, model=deepseek_model)

    if not result.get("success"):
        logger.error(
            "Session summary generation failed",
            extra={"session_id": session.id}
        )
        return None

    result["_models"] = (_, input_model, output_model)
    return result


def _parse_result(result):
    content = (result.get("content") or "").strip()
    if not content:
        logger.warning("Empty AI response for session summary")
        return None

    data = _extract_json(content)

    if not isinstance(data, dict):
        logger.warning("Invalid JSON output from AI")
        return None

    return {
        "content": data.get("content", ""),
        "topics": data.get("topics", []),
    }


def _save_summary(session, parsed):
    with transaction.atomic():
        summary, _ = SessionSummary.objects.update_or_create(
            session=session,
            defaults={
                "content": parsed["content"],
                "topics": parsed["topics"],
                "current": "",  # reset working memory
            },
        )

    return summary


def _extract_json(content: str):
    """
    Extract JSON object from AI output, handles raw JSON or markdown blocks.
    """
    if not content:
        return {}

    content = content.strip()

    # handle```json blocks
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
        logger.warning(
            "JSON decode failed",
            extra={"error": str(e), "content": content}
        )
        return {}


def _record_usage(session, result):
    usage = result.get("usage") or {}
    model_input_cache, model_input, model_output = result.get("_models")

    usage_map = [
        ("input_cached_tokens", model_input_cache),
        ("input_tokens", model_input),
        ("output_tokens", model_output),
    ]

    for key, model in usage_map:
        tokens = usage.get(key)
        if tokens:
            record_usage(
                session=session,
                model=model,
                units=tokens,
            )
