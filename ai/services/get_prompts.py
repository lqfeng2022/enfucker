from ai.models import BasePrompt
from django.core.cache import cache

PROMPT_TTL = 60 * 60 * 24  # 24 hours


def get_host_base_context(profile):
    base = profile.base_prompt
    return None if not base else {
        'name': base.name,
        'content': base.content,
    }


def get_host_persona_context(profile):
    persona = profile.persona_prompt

    return None if not persona else {
        'name': persona.name,
        'role': persona.role,
        'identity': persona.identity,
        'personality': persona.personality,
        'communication_style': persona.communication_style,
        'behavior': persona.behavior,
        'constraints': persona.constraints,
    }


def get_enhancement_instructions(slug='elevenlabs-enhancement'):
    cache_key = f'prompt:db:{slug}'

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    prompt = BasePrompt.objects.filter(slug=slug).first()
    content = prompt.content if prompt else None

    cache.set(cache_key, content, PROMPT_TTL)
    return content
