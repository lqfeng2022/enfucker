from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.prompts.summary import get_summary_prompt
from ai.contracts import SUMMARY
from interact.constants import SUMMARY_WINDOW
from interact.utils.recorder import record_usage
import logging

logger = logging.getLogger(__name__)
logger.debug("SUMMARY MODULE LOADED FROM %s", __file__)


def maybe_summarize_session(*, session):
    """Summarize when unsummarized messages >= SUMMARY_WINDOW"""
    # 1)get all messages
    qs = session.messages.only('id', 'role', 'content', 'created_at')

    # 2)Fetch the target range messages
    if session.summary_upto_message_id:
        qs = qs.filter(id__gt=session.summary_upto_message_id)

    unsummarized = list(qs.order_by('created_at')[:SUMMARY_WINDOW])
    if len(unsummarized) < SUMMARY_WINDOW:
        return  # not enough new messages yet

    lines = []
    for m in unsummarized:
        content = (m.content or '').strip()
        if content:
            lines.append(f"{m.role}: {content}")

    if not lines:
        return

    # 3)Include previous summary(optional) + last `threshold` messages
    text = ''
    if session.summary:
        text += f'Previous summary:\n{session.summary}\n\n'
    text += '\n'.join(lines)

    messages = [
        {"role": "system", "content": get_summary_prompt()},
        {"role": "user", "content": text}
    ]

    # 4)Call LLM for updated summary
    model = resolve_model(profile=session.host.host_profile, usecase=SUMMARY)
    model_input_cache, model_input, model_output = get_summary_model(
        model=model)

    result = deepseek_engine(messages, model=model_output.model.name)
    if not result.get('success', False):
        logger.error('Session summary failed',
                     extra={'session_id': session.id})
        return

    # 5)Save updated summary
    session.summary = (result.get('content') or '').strip()
    session.summary_upto_message = unsummarized[-1]
    session.save(update_fields=['summary', 'summary_upto_message'])

    # 6)Record token usage
    usage = result.get('usage', {}) or {}
    if usage.get('input_cached_tokens'):
        record_usage(session=session, model=model_input_cache,
                     units=usage.get('input_cached_tokens'))
    if usage.get('input_tokens'):
        record_usage(session=session, model=model_input,
                     units=usage['input_tokens'])
    if usage.get('output_tokens'):
        record_usage(session=session, model=model_output,
                     units=usage['output_tokens'])
