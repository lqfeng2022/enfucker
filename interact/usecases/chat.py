from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_chat_model_provider
from ai.services.get_aimodel import resolve_model
from ai.contracts import CHAT
from interact.models import ChatMessage
from interact.tasks import summarize_session_task
from interact.utils.recorder import record_usage
from interact.utils.credits import require_credits
from interact.services.chat_prompts import build_system_prompts
from interact.services.chat_messages import get_chat_context
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
    messages.extend(build_system_prompts(
        host_profile=session.host.host_profile, product=session.product
    ))

    # summary + live window
    if session.summary:
        messages.append({
            "role": "system",
            "content": f"Conversation summary: {session.summary}"
        })
    messages.extend(get_chat_context(session=session))

    print('########## SYSTEM/CHAT PROMPTS DEBUG ##########')
    print(messages)
    print('########## END OF SYSTEM/CHAT PROMPTS DEBUG ##########')

    # 4)Call LLM
    model = resolve_model(profile=session.host.host_profile, usecase=CHAT)
    model_input_cache, model_input, model_output = get_chat_model_provider(
        model=model
    )

    response = deepseek_engine(messages, model=model_output.model.name)

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
        role=ChatMessage.ASSISTANT,
        content=response['content'],
        is_voice=False,  # TTS handled separately
    )

    # 6)Record usage
    usage = response.get('usage', {}) or {}

    if usage.get('input_cached_tokens'):
        record_usage(message=user_msg, model=model_input_cache,
                     units=usage.get('input_cached_tokens'))

    if usage.get('input_tokens'):
        record_usage(message=user_msg, model=model_input,
                     units=usage.get('input_tokens'))

    if usage.get('output_tokens'):
        record_usage(message=assistant_msg, model=model_output,
                     units=usage.get('output_tokens'))

    # 7)async summarization
    summarize_session_task.delay(session.id)

    return assistant_msg
