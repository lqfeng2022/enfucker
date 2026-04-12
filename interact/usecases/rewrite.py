# interact/usecases/rewrite.py
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.prompts.rewrite import get_rewrite_prompt
from ai.contracts import SUMMARY
from interact.utils.recorder import record_usage
from interact.models import MessageRewrite, ChatMessage
import json
import logging

logger = logging.getLogger(__name__)


# Public API
def session_message_rewrite(*, message: ChatMessage):
    if not message:
        return

    prompt_code = _build_prompt_code(message)
    messages = _build_llm_messages(message, prompt_code)

    result = _call_llm(message, messages)
    if not result:
        return None

    parsed = _parse_result(result)
    if not parsed:
        return None

    _save_rewrite(message, parsed)
    _record_usage(message, result)

    return parsed


def _build_prompt_code(message):
    role_code = getattr(message, "role", "user")
    language_code = getattr(message.session, "language", "en")
    return f"{role_code}-{language_code}"


def _build_llm_messages(message, code):
    system_prompt = get_rewrite_prompt(code)

    if not system_prompt:
        logger.warning(
            "Rewrite prompt not found",
            extra={"message_id": message.id, "code": code}
        )
        return None

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message.content},
    ]


def _call_llm(message, messages):
    if not messages:
        return None

    model = resolve_model(
        profile=message.session.host.host_profile,
        usecase=SUMMARY
    )

    model_input_cache, model_input, model_output = get_summary_model(
        model=model)

    result = deepseek_engine(messages, model=model_output.model.name)

    if not result.get("success"):
        logger.error(
            "Rewrite failed",
            extra={"message_id": message.id}
        )
        return None

    result["_models"] = (model_input_cache, model_input, model_output)
    return result


def _parse_result(result):
    content = (result.get("content") or "").strip()
    if not content:
        return None

    data = _extract_json(content)

    if not isinstance(data, list) or not data:
        logger.warning("Invalid rewrite format")
        return None

    item = data[0]

    if not item.get("content"):
        return None

    return {
        "content": item.get("content", ""),
        "vocabulary": _ensure_list(item.get("vocabulary")),
        "phrase": _ensure_list(item.get("phrase")),
        "note": _ensure_list(item.get("note")),
    }


def _save_rewrite(message, parsed):
    rewrite, created = MessageRewrite.objects.update_or_create(
        message=message,
        defaults=parsed,
    )

    logger.debug(
        "Rewrite saved",
        extra={
            "message_id": message.id,
            "created": created,
        }
    )


def _record_usage(message, result):
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
                session=message.session,
                model=model,
                units=tokens,
            )


def _extract_json(content: str):
    """
    Extract JSON array from LLM output (handles markdown + raw JSON).
    """
    if not content:
        return []

    content = content.strip()

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
        return []


def _ensure_list(val):
    return val if isinstance(val, list) else []
