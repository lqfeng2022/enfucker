# interact/usecases/summary_event.py
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.prompts.event import get_event_summary_prompt
from ai.contracts import SUMMARY
from interact.utils.recorder import record_usage
from interact.models import ChatMessage, SessionEvent
import json
import re
import logging

logger = logging.getLogger(__name__)


# Public API
def session_event_summary(*, session, max_events_per_day=5, time_gap_minutes=30):
    """
    Summarize session messages into daily events using time-based chunking.
    Each chunk of messages (<= time_gap_minutes between messages) becomes one event.
    - messages → time chunks → time-aware merge → LLM per chunk → events

    Args:
        session: ChatSession to summarize
        max_events_per_day: Maximum events to create per day
        time_gap_minutes: Minutes between messages to split chunks
    """
    # Get all event_id_isnull messages
    messages = _get_messages(session)
    if not messages:
        return

    # Plit messages into chunks every 30 minutes
    chunks = _build_chunks(messages, time_gap_minutes, max_events_per_day)
    if not chunks:
        return

    # Call LLM for each chunk and create SessionEvent
    for chunk in chunks:
        result = _process_chunk(session, chunk)
        if not result:
            continue

        parsed = _parse_result(result)
        if not parsed:
            continue

        _save_event(session, chunk, parsed)
        _record_usage(session, result)


# Data fetching
def _get_messages(session):
    messages = list(
        session.messages
        .filter(event_id__isnull=True)
        .only("id", "role", "content", "created_at")
        .order_by("created_at")
    )

    if not messages:
        logger.info(
            "No messages for session event summary",
            extra={"session_id": session.id}
        )
        return []

    return [m for m in messages if (m.content or "").strip()]


# Chunk pipeline
def _build_chunks(messages, time_gap_minutes, max_events):
    chunks = _split_by_time(messages, time_gap_minutes)

    chunk_meta = [
        {
            "messages": chunk,
            "start": chunk[0].created_at,
            "end": chunk[-1].created_at,
        }
        for chunk in chunks
    ]

    merged = _merge_chunks(chunk_meta, max_events)
    return [c["messages"] for c in merged]


# Time split
def _split_by_time(messages, gap_minutes):
    chunks = []
    current = []
    last_time = None

    for m in messages:
        if last_time:
            gap = (m.created_at - last_time).total_seconds()
            if gap > gap_minutes * 60:
                if current:
                    chunks.append(current)
                current = []

        current.append(m)
        last_time = m.created_at

    if current:
        chunks.append(current)

    return chunks


# Smart merge
def _merge_chunks(chunks, max_events, max_content=1000):
    """
    Content-driven smart merge/split:
    - Merge small chunks based on nearest neighbor
    - Ensure total chunks <= max_events
    """
    def size(c):
        return sum(len(m.content or "") for m in c["messages"] if m.role == "user")

    # merge small chunks
    i = 0
    while i < len(chunks):
        if size(chunks[i]) < max_content:
            left = size(chunks[i - 1]) if i > 0 else float("inf")
            right = size(chunks[i + 1]) if i < len(chunks) - \
                1 else float("inf")

            if i > 0 and left <= right:
                chunks[i - 1]["messages"] += chunks[i]["messages"]
                chunks[i - 1]["end"] = chunks[i]["end"]
                del chunks[i]
                i -= 1
            elif i < len(chunks) - 1:
                chunks[i]["messages"] += chunks[i + 1]["messages"]
                chunks[i]["end"] = chunks[i + 1]["end"]
                del chunks[i + 1]
            else:
                i += 1
        else:
            i += 1

    # enforce max_events
    while len(chunks) > max_events:
        sizes = [size(c) for c in chunks]
        idx = sizes.index(min(sizes))
        merge_idx = 0 if idx == 0 else idx - 1

        chunks[merge_idx]["messages"] += chunks[merge_idx + 1]["messages"]
        chunks[merge_idx]["end"] = chunks[merge_idx + 1]["end"]
        del chunks[merge_idx + 1]

    return chunks


# Process one chunk
def _process_chunk(session, chunk):
    messages = _build_llm_messages(chunk)
    return _call_llm(session, messages)


def _build_llm_messages(chunk):
    text = "\n".join(
        f"[{m.role.upper()}]\n{(m.content or '').strip()}"
        for m in chunk
    )

    return [
        {"role": "system", "content": get_event_summary_prompt()},
        {"role": "user", "content": text},
    ]


# Call LLM
def _call_llm(session, messages):
    model = resolve_model(
        profile=session.host.host_profile,
        usecase=SUMMARY
    )

    input_cache, input_model, output_model = get_summary_model(model=model)

    result = deepseek_engine(messages, model=output_model.model.name)

    if not result.get("success"):
        logger.error(
            "Event summary failed",
            extra={"session_id": session.id}
        )
        return None

    result["_models"] = (input_cache, input_model, output_model)
    return result


def _extract_json(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # fallback: try to extract JSON block
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                return []
    return []


# Parse result
def _parse_result(result):
    content = (result.get("content") or "").strip()
    if not content:
        return None

    data = _extract_json(content)

    if not isinstance(data, list) or not data:
        return None

    # only take first valid event
    for e in data:
        if e.get("content"):
            return {
                "title": (e.get("title") or "")[:255],
                "content": e.get("content") or "",
                "topics": _ensure_list(e.get("topics")),
            }

    return None


# Save/Update event
def _save_event(session, chunk, parsed):
    message_ids = [m.id for m in chunk]

    existing_event = _find_existing_event(chunk)

    if existing_event:
        existing_event.title = parsed["title"]
        existing_event.content = parsed["content"]
        existing_event.topics = parsed["topics"]
        existing_event.save(
            update_fields=["title", "content", "topics", "updated_at"])

        ChatMessage.objects.filter(
            id__in=message_ids).update(event=existing_event)
        return

    event = SessionEvent.objects.create(
        session=session,
        title=parsed["title"],
        content=parsed["content"],
        topics=parsed["topics"],
    )

    ChatMessage.objects.filter(id__in=message_ids).update(event=event)


# Find existing event
def _find_existing_event(chunk):
    event_ids = {m.event_id for m in chunk if m.event_id}
    if not event_ids:
        return None

    return (
        SessionEvent.objects
        .filter(id__in=event_ids)
        .first()
    )


# Usage tracking
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


def _ensure_list(val):
    return val if isinstance(val, list) else []
