# interact/usecases/current_summary.py
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.prompts.current_summary import get_current_summary_prompt
from ai.contracts import SUMMARY
from interact.constants import SUMMARY_WINDOW
from interact.utils.recorder import record_usage
import logging

logger = logging.getLogger(__name__)


# Public API
def session_current_summary(*, session):
    # get current messages
    unsummarized = _get_unsummarized_messages(session)

    # do nothing when these mesages a less then SUMMARY_WINDOW
    if len(unsummarized) <= SUMMARY_WINDOW:
        return

    # summarize ONLY a moving slice behind the live window
    RECENT_WINDOW = SUMMARY_WINDOW
    OVERLAP_WINDOW = SUMMARY_WINDOW * 2

    if len(unsummarized) <= RECENT_WINDOW:
        return

    # get target messages then put them in a list container
    to_summarize = unsummarized[-OVERLAP_WINDOW:-RECENT_WINDOW]
    lines = _build_lines(to_summarize)

    if not lines:
        return

    # build system prompts and user content
    messages = _build_llm_messages(session, lines)
    result = _call_llm(session, messages)

    if not result:
        return

    _save_summary(session, result)  # save result to DB
    _record_usage(session, result)  # record llm usage to DB


# Helpers
def _get_unsummarized_messages(session):
    return list(
        session.messages
        .filter(event_id__isnull=True)
        .select_related("learning")
        .only("id", "role", "content", "created_at", "learning__content")
        .order_by("created_at")
    )


def _build_lines(messages):
    lines = []

    for m in messages:
        content = _get_message_content(m)
        if not content:
            continue

        if m.role == "user":
            lines.append(f"USER: {content}")
        else:
            lines.append(f"ASSISTANT: {content}")

    return lines


def _get_message_content(message):
    """Prefer rewritten content for user messages"""
    if message.role == "user":
        learning = getattr(message, "learning", None)
        if learning and learning.content:
            return learning.content.strip()
        return (message.content or "").strip()

    return (message.content or "").strip()


def _build_llm_messages(session, lines):
    previous_current = session.sessionsummary.current or ""
    text = "\n\n".join(lines)

    user_input = f"""
    Existing summary:
    {previous_current or "(empty)"}

    New messages:
    {text}

    Update the summary.
    """

    return [
        {"role": "system", "content": get_current_summary_prompt()},
        {"role": "user", "content": user_input},
    ]


def _call_llm(session, messages):
    model = resolve_model(profile=session.host.host_profile, usecase=SUMMARY)
    _, model_input, model_output = get_summary_model(model=model)

    result = deepseek_engine(messages, model=model_output.model.name)

    if not result.get("success"):
        logger.error(
            "Session summary failed",
            extra={"session_id": session.id}
        )
        return None

    result["_models"] = (_, model_input, model_output)

    return result


def _save_summary(session, result):
    summary = session.sessionsummary
    summary.current = (result.get("content") or "").strip()
    summary.save(update_fields=["current"])


def _record_usage(session, result):
    usage = result.get("usage", {}) or {}
    model_input_cache, model_input, model_output = result.get("_models")

    if usage.get("input_cached_tokens"):
        record_usage(session=session, model=model_input_cache,
                     units=usage["input_cached_tokens"])

    if usage.get("input_tokens"):
        record_usage(session=session, model=model_input,
                     units=usage["input_tokens"])

    if usage.get("output_tokens"):
        record_usage(session=session, model=model_output,
                     units=usage["output_tokens"])
