from ai.prompts.enhancement import build_elevenlabs_prompt
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_enhancement_model
from ai.services.get_aimodel import resolve_model
from ai.contracts import ENHANCE
from interact.utils.recorder import record_usage
from interact.utils.credits import require_credits
import logging

logger = logging.getLogger(__name__)


# Optional TTS Enhancement Engine
@require_credits(min_credits=10)
def assistant_tts_enhancement(*, message, is_enhancement=True):
    """
    Apply enhancement tags to assistant message.
    Safe failure: returns None if enhancement fails.
    """
    if not is_enhancement:
        return None

    content = (message.content or '').strip()
    if not content:
        return None

    messages = _build_llm_messages(content)

    result = _call_llm(message, messages)
    if not result:
        _handle_failure(message)
        return None

    enhanced = (result.get("content") or "").strip()
    if not enhanced:
        _handle_failure(message)
        return None

    _save_result(message, enhanced)
    _record_usage(message, result)

    return enhanced


def _build_llm_messages(content: str):
    system_prompt = build_elevenlabs_prompt()

    if not system_prompt:
        raise None

    return [
        {
            "role": "system",
            "content": system_prompt,
            "cache_control": {"type": "persistent"}
            # if supported: helps caching,
            # if not supported: safely ignored
        },
        {
            "role": "user",
            "content": content
        }
    ]


def _call_llm(message, messages):
    if not messages:
        return None

    host_profile = messages.session.host.host_profile
    enhance_model = resolve_model(profile=host_profile, usecase=ENHANCE)
    _, model_input, model_output = get_enhancement_model(model=enhance_model)

    deepseek_model = model_output.model.name
    result = deepseek_engine(messages, model=deepseek_model)

    if not result.get("success"):
        logger.debug(
            "Enhancement failed",
            extra={"message_id": message.id}
        )
        return None

    result["_models"] = (_, model_input, model_output)
    return result


def _save_result(message, enhanced: str):
    message.enhanced_content = enhanced
    message.is_enhancement = True
    message.save(update_fields=["enhanced_content", "is_enhancement"])


def _handle_failure(message):
    message.enhanced_content = None
    message.save(update_fields=["enhanced_content"])


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
