from ai.utils.normalizetext import normalize_text


def build_base_prompt(base_context):
    if not base_context:
        return ''

    blocks = [
        '=== BASE INSTRUCTIONS ===',
        f"# Role: {normalize_text(base_context['name'])}",
        normalize_text(base_context['content']),
        f'# End of Base Instructions'
    ]

    result = normalize_text('\n\n'.join(blocks))

    return result
