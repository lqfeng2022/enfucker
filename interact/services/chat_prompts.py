from ai.prompts.host import build_base_prompt, build_persona_prompt
from ai.prompts.product import build_product_prompt
from store.services.product_context import build_product_context


def build_system_prompts(*, host_profile, product):
    messages = []

    # Build host base promt
    base = host_profile.base_prompt
    if base:
        base = {'name': base.name, 'content': base.content}
        base_prompt = build_base_prompt(base)
        messages.append(
            {"role": "system", "content": base_prompt}
        )

    # Build host persona promt
    persona = host_profile.persona_prompt
    if persona:
        persona = {
            'name': persona.name,
            'role': persona.role,
            'identity': persona.identity,
            'personality': persona.personality,
            'communication_style': persona.communication_style,
            'behavior': persona.behavior,
            'constraints': persona.constraints,
        }
        persona_prompt = build_persona_prompt(persona)
        messages.append(
            {"role": "system", "content": persona_prompt}
        )

    # Build product promt
    product_context = build_product_context(product)
    if product_context:
        product_prompt = build_product_prompt(product_context)
        messages.append(
            {"role": "system", "content": product_prompt}
        )

    return messages
