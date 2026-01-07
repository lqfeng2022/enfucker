from interact.constants import CHAT_CONTEXT_LIMIT


def get_chat_context(*, session):
    """Returns messages AFTER the last summary point."""
    qs = session.messages.filter(visible=True)

    if session.summary_upto_message_id:
        qs = qs.filter(id__gt=session.summary_upto_message_id)

    messages = qs.order_by('-created_at').\
        values('role', 'content')[:CHAT_CONTEXT_LIMIT]

    return list(messages)[::-1]
