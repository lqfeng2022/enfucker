from ai.services.get_prompts import build_host_base_context, build_host_persona_context
from ai.prompts.base import build_base_prompt
from ai.prompts.persona import build_persona_prompt
from ai.prompts.product import build_product_prompt
from store.services.product_context import build_product_context


def build_system_prompts(*, host_profile, product):
    messages = []

    base = build_host_base_context(profile=host_profile)
    if base:
        messages.append({"role": "system", "content": build_base_prompt(base)})

    persona = build_host_persona_context(profile=host_profile)
    if persona:
        messages.append(
            {"role": "system", "content": build_persona_prompt(persona)})

    product_context = build_product_context(product)
    if product_context:
        messages.append(
            {"role": "system", "content": build_product_prompt(product_context)})

    return messages
