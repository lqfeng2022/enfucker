from django.utils import timezone
from interact.constants import CHAT_CONTEXT_LIMIT
from interact.utils.timezone import local_time_for_user
import pytz


TYPE_LABELS = {
    "text": "text",
    "audio": "voice",
    "call": "phone call",
}


# Public API
def get_chat_context(*, session):
    """
    Context strategy:
    - Include ALL messages from today
    - If today's messages < limit → backfill with previous messages
    """

    user_profile = session.user.user_profile

    start_utc = _get_start_of_day_utc(user_profile)

    raw_messages = _fetch_messages(session, start_utc)

    limited_messages = _apply_limit(raw_messages)

    return _format_messages(limited_messages, user_profile)


# start of day
def _get_start_of_day_utc(user_profile):
    now_local = local_time_for_user(timezone.now(), user=user_profile)

    start_of_day = now_local.replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    return start_of_day.astimezone(pytz.UTC)


# fetch + merge logic
def _fetch_messages(session, start_utc):
    qs = session.messages.filter(visible=True).select_related("learning")

    today = list(
        qs.filter(created_at__gte=start_utc)
        .order_by("created_at")
        .values("role", "content", "created_at", "type", "learning__content")[:CHAT_CONTEXT_LIMIT]
    )

    if len(today) >= CHAT_CONTEXT_LIMIT:
        return today

    remaining = CHAT_CONTEXT_LIMIT - len(today)

    history = list(
        qs.filter(created_at__lt=start_utc)
        .order_by("-created_at")
        .values("role", "content", "created_at", "type", "learning__content")[:remaining]
    )[::-1]

    return history + today


# enforce limit properly
def _apply_limit(messages):
    """
    Hard guarantee: never exceed CHAT_CONTEXT_LIMIT
    """
    return messages[-CHAT_CONTEXT_LIMIT:]


# formatting
def _format_messages(raw_messages, user_profile):
    formatted = []

    for m in raw_messages:
        content = (m["content"] or "").strip()
        learning = (m.get("learning__content") or "").strip()

        if learning:
            content = learning

        local_dt = local_time_for_user(m["created_at"], user=user_profile)

        formatted.append({
            "role": m["role"],
            "content": content,
            "type": TYPE_LABELS.get(m["type"], m["type"]),
            "created_at": local_dt.strftime("%Y-%m-%d %H:%M"),
        })

    return formatted
