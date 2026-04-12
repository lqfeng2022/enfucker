# interact/usecases/chat.py
from django.utils import timezone
from ai.engines.llm_chat import qwenplus_engine
from ai.utils.normalizetext import format_text
from ai.services.get_modelprovider import get_chat_model_provider
from ai.services.get_aimodel import resolve_model
from ai.contracts import CHAT
from interact.models import ChatMessage
from interact.utils.recorder import record_usage
from interact.utils.credits import require_credits
from interact.utils.timezone import local_time_for_user
from interact.services.chat_prompts import build_system_prompts
from interact.services.chat_messages import get_chat_context
from interact.tasks import session_current_summary_task
import logging

logger = logging.getLogger(__name__)


# # Public API
@require_credits(min_credits=10)
def get_assistant_message(*, session, user_msg: ChatMessage):
    # validation
    _validate_user_message(user_msg)

    # prompt building
    messages = _build_messages(session, user_msg)

    print("########## PROMPTS DEBUG ##########")
    print(messages)
    print("########## PROMPTS DEBUG ##########")

    # LLM call
    result = _call_llm(session, messages)
    if not result:
        raise RuntimeError("LLM failed")

    # formatting
    content = _normalize_content(result)

    # persistence
    assistant_msg = _save_message(session, user_msg, content)

    # billing
    _record_usage(user_msg, assistant_msg, result)

    # async trigger
    _trigger_async_tasks(session)

    return assistant_msg


# validation
def _validate_user_message(message):
    assert message.role == ChatMessage.USER

    content = (message.content or "").strip()
    if not content:
        logger.warning(
            "Empty user message",
            extra={"message_id": message.id}
        )
        raise ValueError("Empty user message")


# prompt building
def _build_messages(session, user_msg):
    messages = []

    # system prompts
    messages.extend(build_system_prompts(
        host_profile=session.host.host_profile,
        product=session.product
    ))

    # summary prompts
    messages.extend(_build_summary_prompts(session))
    # time prompt
    messages.append(_build_time_prompt(session))
    # chat history
    messages.extend(get_chat_context(session=session))

    return messages


def _build_summary_prompts(session):
    summary = getattr(session, "sessionsummary", None)
    if not summary:
        return []

    memory = []

    if summary.content:
        memory.append(f"SUMMARY:\n{summary.content}")

    if summary.topics:
        memory.append(f"TOPICS:\n{', '.join(summary.topics)}")

    if summary.current:
        memory.append(f"WORKING MEMORY:\n{summary.current}")

    if not memory:
        return []

    return [{
        "role": "system",
        "content": "CONVERSATION MEMORY:\n\n" + "\n\n".join(memory)
    }]


def _build_time_prompt(session):
    dt = timezone.now()
    user_profile = session.user.user_profile
    local_dt = local_time_for_user(dt=dt, user=user_profile)

    return {
        "role": "system",
        "content": (
            f"Current time: {local_dt.strftime('%Y-%m-%d %H:%M')}\n"
            "Each message has a timestamp and type (text, voice, call). "
            "Use this information naturally, but do not include timestamps unless asked."
        )
    }


# LLM call
def _call_llm(session, messages):
    model = resolve_model(
        profile=session.host.host_profile,
        usecase=CHAT
    )

    model_input, model_output = get_chat_model_provider(model=model)

    result = qwenplus_engine(messages, model=model_output.model.name)

    if not result.get("success"):
        logger.error(
            "LLM failure",
            extra={
                "session_id": session.id,
                "model": model_output.model.name,
                "error": result.get("error"),
            }
        )
        return None

    result["_models"] = (model_input, model_output)
    return result


# formatting
def _normalize_content(result):
    content = result.get("content") or ""
    return format_text(content)


# persistence
def _save_message(session, user_msg, content):
    return ChatMessage.objects.create(
        session=session,
        call_session=user_msg.call_session,
        role=ChatMessage.ASSISTANT,
        content=content,
        is_voice=False,
    )


# billing
def _record_usage(user_msg, assistant_msg, result):
    usage = result.get("usage") or {}
    model_input, model_output = result.get("_models")

    usage_map = [
        ("input_tokens", model_input, user_msg),
        ("output_tokens", model_output, assistant_msg),
    ]

    for key, model, owner in usage_map:
        tokens = usage.get(key)
        if tokens:
            record_usage(
                message=owner,
                model=model,
                units=tokens,
            )


# async trigger
def _trigger_async_tasks(session):
    session_current_summary_task.delay(session.id)
