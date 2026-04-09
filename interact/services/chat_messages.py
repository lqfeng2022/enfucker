from django.utils import timezone
from interact.constants import CHAT_CONTEXT_LIMIT
from interact.utils.timezone import local_time_for_user
import pytz


TYPE_LABELS = {
    "text": "text",
    "audio": "voice",
    "call": "phone call",
}


def get_chat_context(*, session):
    """
    Context strategy:
    1. Include ALL messages from today
    2. If today's messages < limit → backfill with previous messages
    """

    queryset = session.messages.filter(visible=True)

    # --- Step 1: Get user's today range ---
    user_profile = session.user.user_profile
    now_local = local_time_for_user(dt=timezone.now(), user=user_profile)

    start_of_day = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    start_utc = start_of_day.astimezone(pytz.UTC)

    # --- Step 2: Get today's messages ---
    today_qs = queryset.select_related('learning').filter(created_at__gte=start_utc). \
        order_by("created_at")
    today_messages = list(
        today_qs.values("role", "content", "created_at",
                        "type", "learning__content")
    )

    # --- Step 3: If today messages < limit → backfill ---
    if len(today_messages) < CHAT_CONTEXT_LIMIT:
        remaining = CHAT_CONTEXT_LIMIT - len(today_messages)

        previous_qs = (
            queryset.select_related('learning').filter(
                created_at__lt=start_utc)
            .order_by("-created_at")
            .values("role", "content", "created_at", "type", "learning__content")[:remaining]
        )

        previous_messages = list(previous_qs)[::-1]  # oldest → newest
        raw_messages = previous_messages + today_messages
    else:
        # --- Step 4: If today messages exceed limit → keep ALL ---
        raw_messages = today_messages

    # --- Step 5: Format messages ---
    formatted_messages = []

    for m in raw_messages:
        local_dt = local_time_for_user(dt=m["created_at"], user=user_profile)
        content = (m["content"] or "").strip()
        learning_content = (m.get("learning__content") or "").strip()

        if learning_content:
            content = learning_content

        formatted_messages.append({
            "role": m["role"],
            "content": content,
            "type": TYPE_LABELS.get(m["type"], m["type"]),
            "created_at": local_dt.strftime('%Y-%m-%d %H:%M')
        })

    return formatted_messages
