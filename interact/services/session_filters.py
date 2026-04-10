# interact/services/session_filters.py
from interact.models import ChatSession


def get_sessions_for_event_summary():
    """
    Return session IDs whose latest message falls into *yesterday*
    in the user's local timezone.
    """
    sessions = (
        ChatSession.objects
        .filter(messages__event_id__isnull=True)
        .distinct()
        .values_list("id", flat=True)
    )

    return sessions
