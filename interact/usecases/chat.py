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


@require_credits(min_credits=10)
def get_assistant_message(*, session, user_msg: ChatMessage):
    # 1)ASSERT USER role
    assert user_msg.role == ChatMessage.USER

    # 2)Validate user content (FINAL GATE)
    user_text = (user_msg.content or '').strip()
    if not user_text:
        logger.warning(
            'Skipping LLM call due to empty user content',
            extra={'session_id': session.id, 'message_id': user_msg.id, }
        )
        return None

    # 3)ADD system/chat prompts + latest 30 messages
    messages = []

    # Existing system prompts (host, product)
    messages.extend(build_system_prompts(
        host_profile=session.host.host_profile,
        product=session.product
    ))

    # Conversation summary (new SessionSummary)
    summary = getattr(session, "sessionsummary", None)

    if summary and summary.content:
        messages.append({
            "role": "system",
            "content": f"Conversation Summary:\n{summary.content}"
        })

    if summary and summary.topics:
        topics_str = ", ".join(summary.topics)
        messages.append({
            "role": "system",
            "content": f"Conversation Topics:\n{topics_str}"
        })

    # Current time system prompt
    dt = timezone.now()  # UTC
    user_profile = session.user.user_profile  # user_profile
    local_dt = local_time_for_user(dt=dt, user=user_profile)

    messages.append({
        "role": "system",
        "content": (
            f"Current time: {local_dt.strftime("%Y-%m-%d %H:%M")}\n"
            "Each message has a timestamp and type (text, voice, call). "
            "Use this information to understand timing and communication context naturally, "
            "but do not include the timestamps in your responses unless explicitly asked."
        )
    })

    # Latest chat messages
    raw_messages = get_chat_context(session=session)

    messages.extend(raw_messages)

    print("########## PROMPTS DEBUG ##########")
    print(messages)
    print("########## END OF PROMPTS DEBUG ##########")

    # 4)Call LLM
    model = resolve_model(profile=session.host.host_profile, usecase=CHAT)
    model_input, model_output = get_chat_model_provider(model=model)

    response = qwenplus_engine(messages, model=model_output.model.name)

    # ensure all callers receive formatted text regardless of engine output
    if response.get('content'):
        response['content'] = format_text(response['content'])

    if not response.get('success'):
        logger.error('LLM failure', extra={
            'session_id': session.id,
            'model': model_output.model.name,
            'error': response.get('error'),
        })
        # Prevent KeyError when response has no 'content' (failure case)
        raise RuntimeError(response.get('error') or 'LLM failure')

    # 5)Persist assistant message
    assistant_msg = ChatMessage.objects.create(
        session=session,
        call_session=user_msg.call_session,  # 🔥 MUST be here
        role=ChatMessage.ASSISTANT,
        content=response['content'],
        is_voice=False,  # TTS handled separately
    )

    # 6)Record usage
    usage = response.get('usage', {}) or {}

    # if usage.get('input_cached_tokens'):
    #     record_usage(message=user_msg, model=model_input_cache,
    #                  units=usage.get('input_cached_tokens'))

    if usage.get('input_tokens'):
        record_usage(message=user_msg, model=model_input,
                     units=usage.get('input_tokens'))

    if usage.get('output_tokens'):
        record_usage(message=assistant_msg, model=model_output,
                     units=usage.get('output_tokens'))

    session_current_summary_task.delay(session.id)

    return assistant_msg
