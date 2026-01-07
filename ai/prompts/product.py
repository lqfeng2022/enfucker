from ai.utils.normalizetext import normalize_text


def build_product_prompt(product_context: dict | None):
    blocks = [
        '=== TOPIC CONTEXT ===',
        f"# Topic type: {
            product_context['type'] if product_context else 'a FREE topic'
        }"
    ]

    if product_context['type'] == 'Expression':
        blocks.append(f"# Expression: {product_context.get('expression')}")

        if product_context.get('subtitle'):
            blocks.append(
                f"# Subtitle:\n{normalize_text(product_context['subtitle'])}"
            )
        if product_context.get('video'):
            blocks.append(
                f"# Video:\n{normalize_text(product_context['video'])}"
            )

    elif product_context['type'] == 'Subtitle':
        blocks.append(
            f"# Subtitle:\n{normalize_text(product_context.get('subtitle'))}"
        )
        if product_context.get('video'):
            blocks.append(
                f"# Video:\n{normalize_text(product_context['video'])}"
            )

    elif product_context['type'] == 'Video':
        if product_context.get('video'):
            blocks.append(
                f"# Video:\n{normalize_text(product_context['video'])}"
            )

    blocks.append(f"# End of Topic Context")

    result = normalize_text(
        '\n\n'.join(b.strip() for b in blocks if b and b.strip())
    )
    return result
