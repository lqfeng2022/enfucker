def add_latest_messages(messages):
    """Convert a list of message dicts into LLM-ready format.
    Each message dict must have 'role' and 'content' keys.
    """
    if not messages:
        return []

    result = []
    for msg in messages:
        role = msg.get('role')
        content = (msg.get('content') or '').strip()
        if role and content:
            result.append({"role": role, "content": content})
    return result
