from interact.constants import CHAT_CONTEXT_LIMIT


# LLM communication quality
TYPE_LABELS = {
    "text": "text",
    "audio": "voice",
    "call": "phone call",
}


def get_chat_context(*, session):
    """Returns messages AFTER the last summary point."""
    queryset = session.messages.filter(visible=True)

    if session.summary_upto_message_id:
        queryset = queryset.filter(id__gt=session.summary_upto_message_id)

    raw_messages = (
        queryset.order_by('-created_at')  # newest → oldest
        .values('role', 'content', 'created_at', 'type')[:CHAT_CONTEXT_LIMIT]
    )

    formatted_messages = []
    for m in raw_messages:
        formatted_messages.append({
            "role": m["role"],
            "content": (m["content"] or "").strip(),
            "type": TYPE_LABELS.get(m["type"], m["type"]),
            "created_at": m['created_at'].strftime('%Y-%m-%d %H:%M')
        })

    return list(formatted_messages)[::-1]  # oldest → newest
