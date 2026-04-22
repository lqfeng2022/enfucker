from ai.utils.normalizetext import normalize_text


def build_host_prompt(base_context, persona_context):
    blocks = []

    # BASE
    if base_context and base_context.get("content"):
        base_blocks = [
            f"# BASE INSTRUCTIONS",
            normalize_text(base_context["content"])
        ]

        blocks.append('\n\n'.join(
            [b.strip() for b in base_blocks if b and b.strip()]
        ))

    # PERSONA
    if persona_context:
        persona_blocks = [
            f"# PERSONA INSTRUCTIONS",
            normalize_text(persona_context.get("identity")),
            normalize_text(persona_context.get("personality")),
            normalize_text(persona_context.get("communication_style")),
            normalize_text(persona_context.get("behavior")),
            normalize_text(persona_context.get("constraints")),
        ]

        blocks.append('\n\n'.join(
            [b.strip() for b in persona_blocks if b and b.strip()]
        ))

    return normalize_text('\n\n\n'.join(blocks))
