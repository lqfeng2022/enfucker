# interact/services/session_filters.py
from datetime import timedelta
from django.utils import timezone
from django.db.models import Max
from interact.models import ChatSession
import pytz


def get_sessions_for_event_summary():
    """
    Return session IDs whose latest message falls into *yesterday*
    in the user's local timezone.
    """

    # --- Step 1: coarse DB filter (limit dataset) ---
    now = timezone.now()
    cutoff = now - timedelta(days=2)  # safety window

    sessions = (
        ChatSession.objects
        .annotate(last_msg_at=Max("messages__created_at"))
        .filter(last_msg_at__gte=cutoff)
        .select_related("user__user_profile")
    )

    result_ids = []

    for session in sessions:
        last_msg_at = session.last_msg_at
        if not last_msg_at:
            continue

        # --- Step 2: user timezone ---
        tz_str = getattr(session.user.user_profile, "timezone", "UTC")

        try:
            user_tz = pytz.timezone(tz_str)
        except Exception:
            user_tz = pytz.UTC

        # --- Step 3: convert to user local time ---
        local_dt = last_msg_at.astimezone(user_tz)

        # --- Step 4: compute "yesterday" in user timezone ---
        now_local = timezone.now().astimezone(user_tz)
        yesterday = (now_local - timedelta(days=1)).date()

        # --- Step 5: compare ---
        if local_dt.date() == yesterday:
            result_ids.append(session.id)

    return result_ids
