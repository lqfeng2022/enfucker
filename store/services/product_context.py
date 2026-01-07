def build_product_context(product):
    if not product:
        return None

    if product.type == 'video':
        return {
            'type': 'Video',
            'video': product.video.context,
        }

    if product.type == 'subtitle':
        return {
            'type': 'Subtitle',
            'subtitle': product.subtitle.content,
            'video': getattr(product.subtitle.video, 'context', None),
        }

    if product.type == 'expression':
        subtitle = product.expression.subtitle
        video = getattr(subtitle, 'video', None)

        return {
            'type': 'Expression',
            'expression': product.expression.title,
            'subtitle': subtitle.content if subtitle else None,
            'video': video.context if video else None,
        }

    return None
