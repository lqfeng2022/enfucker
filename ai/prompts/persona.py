from ai.utils.normalizetext import normalize_text


def build_persona_prompt(persona_context):
    if not persona_context:
        return ''

    blocks = [
        '=== PERSONA INSTRUCTIONS ===',
        f"# You are {persona_context['name']}, {persona_context['role']}.",
        normalize_text(persona_context['identity']),
        normalize_text(persona_context['personality']),
        normalize_text(persona_context['communication_style']),
        normalize_text(persona_context['behavior']),
        normalize_text(persona_context['constraints']),
        f'# End of Persona Instructions'
    ]

    result = normalize_text('\n\n'.join(
        [b.strip() for b in blocks if b and b.strip()]
    ))

    return result
