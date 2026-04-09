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
logger.debug("SUMMARY MODULE LOADED FROM %s", __file__)


def session_message_rewrite(*, message: ChatMessage):
    if not message:
        logger.info("No messages for session event summary")
        return

    # Use the prompt code from message and message.session
    role_code = getattr(message, "role", "user")
    language_code = getattr(message.session, "language", "en")
    code = f"{role_code}-{language_code}"

    print("########## DEBUG CODE ##########")
    print(code)
    print(get_rewrite_prompt(code))
    print("########## DEBUG CODE ##########")

    # build prompts (system + messages)
    messages_payload = [
        {"role": "system", "content": get_rewrite_prompt(code)},
        {"role": "user", "content": message.content}
    ]

    # Call LLM for updated summary
    model = resolve_model(
        profile=message.session.host.host_profile,
        usecase=SUMMARY
    )
    input_cache, input, output = get_summary_model(model=model)

    result = deepseek_engine(messages_payload, model=output.model.name)
    if not result.get('success', False):
        logger.error('Session summary failed')
        return

    # Extract json data then store in DB
    content = result.get('content') or ''
    print("########## DEBUG CODE ##########")
    print(content)
    print("########## DEBUG CODE ##########")
    _parse_and_rewrite_message(message=message, content=content)

    # Record token usage
    usage = result.get('usage', {}) or {}
    if usage.get('input_cached_tokens'):
        record_usage(session=message.session, model=input_cache,
                     units=usage.get('input_cached_tokens'))
    if usage.get('input_tokens'):
        record_usage(session=message.session, model=input,
                     units=usage['input_tokens'])
    if usage.get('output_tokens'):
        record_usage(session=message.session, model=output,
                     units=usage['output_tokens'])


def _parse_and_rewrite_message(*, message, content: str):
    """Parse LLM JSON result and store/update MessageRewrite object (one-to-one)."""
    learning_data = _extract_json(content)
    print("########## DEBUG CODE ##########")
    print(learning_data)
    print("########## DEBUG CODE ##########")
    if not isinstance(learning_data, list):
        logger.warning("Invalid learning format")
        return

    # Only take the first item since it's one-to-one
    e = learning_data[0]
    if not e.get("content"):
        logger.warning("Learning content empty, skipped",
                       extra={"message_id": message.id})
        return

    # Update existing rewrite or create a new one
    rewrite, created = MessageRewrite.objects.update_or_create(
        message=message,
        defaults={
            "content": e.get("content", ""),
            "vocabulary": _ensure_list(e.get("vocabulary")),
            "phrase": _ensure_list(e.get("phrase")),
            "note": _ensure_list(e.get("note")),
        },
    )

    action = "Created" if created else "Updated"
    logger.debug(f"{action} rewrite for message {message.id}")


def _extract_json(content: str):
    """Extract JSON array from LLM output (handles markdown + raw JSON)."""
    if not content:
        return []

    content = content.strip()

    # Case 1: markdown ```json ... ```
    if content.startswith("```"):
        lines = content.splitlines()

        # remove first line ``` or ```json
        if lines[0].startswith("```"):
            lines = lines[1:]

        # remove last line ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        content = "\n".join(lines).strip()

    # Now it should be pure JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("JSON decode failed", extra={
                       "error": str(e), "content": content})
        return []


def _ensure_list(val):
    if isinstance(val, list):
        return val
    return []
