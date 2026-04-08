# interact/usecases/summary_event.py
from datetime import timedelta, datetime
from django.utils import timezone
from ai.engines.llm_chat import deepseek_engine
from ai.services.get_modelprovider import get_summary_model
from ai.services.get_aimodel import resolve_model
from ai.prompts.event import get_event_summary_prompt
from ai.contracts import SUMMARY
from interact.utils.recorder import record_usage
from interact.models import ChatMessage, SessionEvent
import pytz
import json
import re
import logging

logger = logging.getLogger(__name__)
logger.debug("SUMMARY MODULE LOADED FROM %s", __file__)


def session_event_summary(*, session, max_events_per_day=5, time_gap_minutes=30, target_date=None):
    """
    Summarize session messages into daily events using time-based chunking.
    Each chunk of messages (<= time_gap_minutes between messages) becomes one event.
    - messages → time chunks → time-aware merge → LLM per chunk → events

    Args:
        session: ChatSession to summarize
        max_events_per_day: Maximum events to create per day
        time_gap_minutes: Minutes between messages to split chunks
        target_date: Date to summarize (datetime.date or None for yesterday)
    """
    # Get all messages
    qs = session.messages.only('id', 'role', 'content', 'created_at'). \
        order_by('created_at')

    # Get target messages
    # Get the start and end of target date in user's local time
    user_tz_str = getattr(session.user.user_profile, 'timezone', 'UTC')
    user_tz = pytz.timezone(user_tz_str)  # what if user_tz_str is invalid

    now_utc = timezone.now()
    now_local = now_utc.astimezone(user_tz)

    # Use target_date if provided, otherwise use yesterday
    if target_date:
        target_local = user_tz.localize(
            datetime.combine(target_date, datetime.min.time()))
    else:
        # Default to yesterday
        start_of_today = now_local.replace(
            hour=0, minute=0, second=0, microsecond=0)
        target_local = start_of_today - timedelta(days=1)

    start = target_local
    end = target_local + timedelta(days=1)

    # Convert boundaries back to UTC
    start_utc = start.astimezone(pytz.UTC)
    end_utc = end.astimezone(pytz.UTC)

    messages = list(qs.filter(created_at__gte=start_utc,
                              created_at__lt=end_utc))
    if not messages:
        logger.info("No messages for session event summary",
                    extra={"session_id": session.id})
        return

    # Plit messages into chunks every 30 minutes
    chunks = _get_chunks(messages=messages, time_gap_minutes=time_gap_minutes)

    # Limit number of events per day
    chunk_meta = [
        {
            "messages": chunk,
            "start": chunk[0].created_at,
            "end": chunk[-1].created_at,
        } for chunk in chunks
    ]

    chunks = _merge_chunks_smart_content(chunk_meta, max_events_per_day)
    chunks = [c["messages"] for c in chunks]

    # --- Call LLM for each chunk and create SessionEvent ---
    for chunk in chunks:
        chunk_text = "\n".join(
            f"[{m.role.upper()}]\n{m.content.strip()}" for m in chunk
        )

        # build prompts (system + messages)
        messages_payload = [
            {"role": "system", "content": get_event_summary_prompt()},
            {"role": "user", "content": chunk_text}
        ]

        # Call LLM for updated summary
        model = resolve_model(
            profile=session.host.host_profile,
            usecase=SUMMARY
        )
        input_cache, input, output = get_summary_model(model=model)

        result = deepseek_engine(messages_payload, model=output.model.name)
        if not result.get('success', False):
            logger.error('Session summary failed',
                         extra={'session_id': session.id})
            continue

        # Extract json data then store in DB
        content = result.get('content') or ''
        if not content.strip():
            logger.warning("Empty LLM response", extra={
                           "session_id": session.id})
            continue
        _parse_and_create_session_events(session=session, content=content,
                                         chunk_messages=chunk)

        # Record token usage
        usage = result.get('usage', {}) or {}
        if usage.get('input_cached_tokens'):
            record_usage(session=session, model=input_cache,
                         units=usage.get('input_cached_tokens'))
        if usage.get('input_tokens'):
            record_usage(session=session, model=input,
                         units=usage['input_tokens'])
        if usage.get('output_tokens'):
            record_usage(session=session, model=output,
                         units=usage['output_tokens'])


def _get_chunks(*, messages, time_gap_minutes=30):
    chunks = []
    current_chunk = []
    last_time = None

    for m in messages:
        if not m.content.strip():
            continue

        if last_time is not None:
            chunk_gap = (m.created_at - last_time).total_seconds()
            if last_time and chunk_gap > time_gap_minutes * 60:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = []

        current_chunk.append(m)
        last_time = m.created_at

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _merge_chunks_smart_content(chunks, max_events, max_message_content=1000):
    """
    Content-driven smart merge/split:
    1. Merge small chunks based on nearest neighbor
    2. Ensure total chunks <= max_events
    """

    def chunk_content_size(chunk):
        # Only count user messages
        return sum(len(m.content or '') for m in chunk["messages"] if m.role == "user")

    # --- Step 1: Merge small chunks by nearest neighbor ---
    i = 0
    while i < len(chunks):
        size_i = chunk_content_size(chunks[i])

        if size_i < max_message_content:
            # determine which neighbor to merge with
            merge_with_left = False
            merge_with_right = False

            if i > 0:
                merge_with_left = True
                left_size = chunk_content_size(chunks[i - 1])
            else:
                left_size = float('inf')

            if i < len(chunks) - 1:
                merge_with_right = True
                right_size = chunk_content_size(chunks[i + 1])
            else:
                right_size = float('inf')

            # pick neighbor with smaller size to balance chunks
            if left_size <= right_size and merge_with_left:
                # merge with left
                chunks[i - 1]["messages"].extend(chunks[i]["messages"])
                chunks[i - 1]["end"] = chunks[i]["end"]

                del chunks[i]
                i -= 1  # stay on merged chunk
            elif merge_with_right:
                # merge with right
                chunks[i]["messages"].extend(chunks[i + 1]["messages"])
                chunks[i]["end"] = chunks[i + 1]["end"]

                del chunks[i + 1]
                # stay at current i to check further merges
            else:
                # no neighbor to merge, move forward
                i += 1
        else:
            i += 1

    # --- Step 2: Ensure max_events ---
    while len(chunks) > max_events:
        # merge the smallest chunk with neighbor
        sizes = [chunk_content_size(c) for c in chunks]
        smallest_idx = sizes.index(min(sizes))

        merge_idx = 0 if smallest_idx == 0 else smallest_idx - 1

        chunks[merge_idx]["messages"].extend(chunks[merge_idx + 1]["messages"])
        chunks[merge_idx]["end"] = chunks[merge_idx + 1]["end"]

        del chunks[merge_idx + 1]

    return chunks


def _parse_and_create_session_events(*, session, content: str, chunk_messages: list):
    """
    Parse LLM JSON result and store SessionEvent objects.
    Also assign the chunk messages to the created event.
    """
    events_data = _extract_json(content)
    if not isinstance(events_data, list) or not events_data:
        logger.warning("Invalid events format",
                       extra={"session_id": session.id})
        return

    # If any message already has an event, update that existing event
    existing_event_ids = {m.event_id for m in chunk_messages if m.event_id}
    existing_event = None
    if existing_event_ids:
        if len(existing_event_ids) > 1:
            logger.warning(
                "Chunk has messages from multiple events, using first",
                extra={"session_id": session.id,
                       "event_ids": list(existing_event_ids)}
            )
        existing_event = ChatMessage.objects.filter(
            event_id__in=existing_event_ids
        ).values_list('event_id', flat=True).first()
        if existing_event:
            existing_event = SessionEvent.objects.get(id=existing_event)

    # Use the first valid event payload only; each chunk should map to one event.
    event_payload = None
    for e in events_data:
        if e.get('content'):
            event_payload = e
            break

    if not event_payload:
        return

    if existing_event:
        existing_event.title = (event_payload.get('title') or '')[:255]
        existing_event.content = (event_payload.get('content') or '')
        existing_event.topics = _ensure_list(event_payload.get('topics'))
        existing_event.save(
            update_fields=['title', 'content', 'topics', 'updated_at']
        )
        ChatMessage.objects.filter(id__in=[m.id for m in chunk_messages]).update(
            event=existing_event
        )
        return

    event = SessionEvent(
        session=session,
        title=(event_payload.get('title') or '')[:255],
        content=(event_payload.get('content') or ''),
        topics=_ensure_list(event_payload.get('topics')),
    )
    event.save()
    ChatMessage.objects.filter(
        id__in=[m.id for m in chunk_messages]).update(event=event)


def _extract_json(content: str):
    """Extract JSON array from LLM output."""
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


def _ensure_list(val):
    return val if isinstance(val, list) else []
