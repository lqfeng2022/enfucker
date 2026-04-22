from ai.prompts.host import build_host_prompt
from ai.prompts.product import build_product_prompt
from store.services.product_context import build_product_context


def build_system_prompts(*, host_profile, product):
    messages = []

    # Prepare base
    base = host_profile.base_prompt
    base_context = None
    if base:
        base_context = {
            'name': base.name,
            'content': base.content,
        }

    # Prepare persona
    persona = host_profile.persona_prompt
    persona_context = None
    if persona:
        persona_context = {
            'identity': persona.identity,
            'personality': persona.personality,
            'communication_style': persona.communication_style,
            'behavior': persona.behavior,
            'constraints': persona.constraints,
        }

    # Merge into ONE system message
    host_prompt = build_host_prompt(base_context, persona_context)
    if host_prompt:
        messages.append({
            "role": "system",
            "content": host_prompt
        })

    # Product stays separate (optional)
    product_context = build_product_context(product)
    if product_context:
        product_prompt = build_product_prompt(product_context)
        messages.append({
            "role": "system",
            "content": product_prompt
        })

    return messages
