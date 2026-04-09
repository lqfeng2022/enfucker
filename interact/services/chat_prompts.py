from ai.services.get_prompts import build_base_context, build_persona_context
from ai.prompts.host import build_base_prompt, build_persona_prompt
from ai.prompts.product import build_product_prompt
from store.services.product_context import build_product_context


def build_system_prompts(*, host_profile, product):
    messages = []

    base = build_base_context(profile=host_profile)
    if base:
        messages.append({"role": "system", "content": build_base_prompt(base)})

    persona = build_persona_context(profile=host_profile)
    if persona:
        messages.append(
            {"role": "system", "content": build_persona_prompt(persona)})

    product_context = build_product_context(product)
    if product_context:
        messages.append(
            {"role": "system", "content": build_product_prompt(product_context)})

    return messages
