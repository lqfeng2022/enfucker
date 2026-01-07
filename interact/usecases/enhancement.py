from ai.prompts.enhancement import build_elevenlabs_prompt
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_enhancement_model
from ai.services.get_aimodel import resolve_model
from ai.contracts import ENHANCE
from ai.services.get_prompts import get_enhancement_instructions
from interact.utils.recorder import record_usage
from interact.utils.credits import require_credits
import logging

logger = logging.getLogger(__name__)


# Optional TTS Enhancement Engine
@require_credits(min_credits=10)
def assistant_tts_enhancement(*, message, is_enhancement=True):
    """Apply enhancement tags to assistant message.
    Safe failure: returns None if enhancement fails.
    """
    if not is_enhancement:
        return None

    content = (message.content or '').strip()
    if not content:
        return None

    try:
        enhanced_text = enhancement_engine(message=message, content=content)
    except EnhancementError as e:
        logger.debug(
            'Enhancement skipped',
            extra={'message_id': message.id, 'reason': str(e)}
        )

        # expected, non-fatal
        message.enhanced_content = None
        message.save(update_fields=['enhanced_content'])
        return None

    message.enhanced_content = enhanced_text
    message.is_enhancement = True
    message.save(update_fields=['enhanced_content', 'is_enhancement'])

    return enhanced_text


def enhancement_engine(*, message, content: str) -> str:
    model = resolve_model(profile=message.session.host.host_profile,
                          usecase=ENHANCE)
    model_input_cache, model_input, model_output = get_enhancement_model(
        model=model)

    instructions_text = get_enhancement_instructions()
    system_prompt = build_elevenlabs_prompt(instructions_text)

    if not system_prompt:
        raise EnhancementError('Enhancement instructions not found.')

    messages = [
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

    print('########## ENHANCEMENT PROMPTS DEBUG ##########')
    print(messages)
    print('########## END OF ENHANCEMENT PROMPTS DEBUG ##########')

    response = deepseek_engine(messages, model=model_output.model.name)

    if not response.get('success'):
        raise EnhancementError(response.get('error') or 'Enhancement failed.')

    # Record usage at MESSAGE level
    usage = response.get('usage', {}) or {}

    if usage.get('input_cached_tokens'):
        record_usage(message=message, model=model_input_cache,
                     units=usage.get('input_cached_tokens'))

    if usage.get('input_tokens'):
        record_usage(message=message, model=model_input,
                     units=usage.get('input_tokens'))

    if usage.get('output_tokens'):
        record_usage(message=message, model=model_output,
                     units=usage.get('output_tokens'))

    enhanced = (response.get('content') or '').strip()
    if not enhanced:
        raise EnhancementError('Empty enhancement result.')

    return enhanced


class EnhancementError(RuntimeError):
    """Non-fatal enhancement failure."""
    pass
