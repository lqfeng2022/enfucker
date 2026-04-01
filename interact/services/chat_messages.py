from interact.constants import CHAT_CONTEXT_LIMIT


# LLM communication quality
TYPE_LABELS = {
    "text": "text",
    "audio": "voice",
    "call": "phone call",
}


def get_chat_context(*, session):
    """Returns messages AFTER the last summary point with LLM-visible metadata."""
    queryset = session.messages.filter(visible=True)

    if session.summary_upto_message_id:
        queryset = queryset.filter(id__gt=session.summary_upto_message_id)

    messages = (
        queryset.order_by('-created_at')
        .values('role', 'content', 'created_at', 'type')[:CHAT_CONTEXT_LIMIT]
    )

    return [
        {
            "role": m["role"],
            # created_at/type: LLM awareness
            "content": (
                f"[{TYPE_LABELS.get(m['type'], m['type'])} | "
                f"{m['created_at'].strftime('%Y-%m-%d %H:%M')}] "
                f"{(m['content'] or '').strip()}"
            ),
            # metadata: system intelligence
            "metadata": {
                "created_at": m["created_at"].isoformat(),
                "type": m["type"],
            },
        }
        for m in list(messages)[::-1]  # oldest → newest
    ]


# Message example reference
# {
#   "role": "user",
#   "content": "[voice | 2026-04-01 10:15] Hey, can you help me with this product?",
#   "metadata": {
#     "type": "audio",
#     "created_at": "2026-04-01T10:15:23Z"
#   }
# }

# {
#   "role": "assistant",
#   "content": "[text | 2026-04-01 10:15] Sure! What would you like to know?",
#   "metadata": {
#     "type": "text",
#     "created_at": "2026-04-01T10:15:25Z"
#   }
# }

# {
#   "role": "user",
#   "content": "[call | 2026-04-01 10:16] Yeah I'm looking at the product page now",
#   "metadata": {
#     "type": "call",
#     "created_at": "2026-04-01T10:16:02Z"
#   }
# }