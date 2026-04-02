from interact.constants import CHAT_CONTEXT_LIMIT
from interact.utils.timezone import local_time_for_user


# LLM communication quality
TYPE_LABELS = {
    "text": "text",
    "audio": "voice",
    "call": "phone call",
}


def get_chat_context(*, session):
    """Returns messages AFTER the last summary point."""
    queryset = session.messages.filter(visible=True)

    raw_messages = (
        queryset.order_by('-created_at')  # newest → oldest
        .values('role', 'content', 'created_at', 'type')[:CHAT_CONTEXT_LIMIT]
    )

    formatted_messages = []

    for m in raw_messages:
        # Convert UTC datatime to local datatime
        dt = m['created_at']  # UTC
        user_profile = session.user.user_profile  # user_profile
        local_dt = local_time_for_user(dt=dt, user=user_profile)

        formatted_messages.append({
            "role": m["role"],
            "content": (m["content"] or "").strip(),
            "type": TYPE_LABELS.get(m["type"], m["type"]),
            "created_at": local_dt.strftime('%Y-%m-%d %H:%M')
        })

    return list(formatted_messages)[::-1]  # oldest → newest
