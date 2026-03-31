from openai import OpenAI
from decimal import Decimal
from django.conf import settings


def deepseek_engine(messages, *, model: str):
    client = OpenAI(api_key=settings.DEEPSEEK_API_KEY,
                    base_url=settings.DEEPSEEK_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            # max_tokens=250,
            temperature=0.8,
        )

        # DeepSeek/OpenAI Python SDK returns response.usage as a Pydantic object, not a dict.
        # So we gotta convert usage to plain dict
        content = response.choices[0].message.content.strip()

        input_cache_hit_tokens = Decimal(
            (response.usage.prompt_cache_hit_tokens) / 1000)
        input_cache_miss_tokens = Decimal(
            (response.usage.prompt_cache_miss_tokens) / 1000)
        output_tokens = Decimal((response.usage.completion_tokens) / 1000)

        usage = {
            'input_tokens': input_cache_miss_tokens,
            'input_cached_tokens': input_cache_hit_tokens,
            'output_tokens': output_tokens,
        }

        return {'success': True, 'content': content, 'usage': usage}

    except Exception as e:
        return {'success': False, 'error': f'[LLM ERROR] {str(e)}'}


def qwenplus_engine(messages, *, model: str):
    client = OpenAI(api_key=settings.QWEN_API_KEY,
                    base_url=settings.QWEN_BASE_URL)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )

        content = response.choices[0].message.content.strip()

        # safe usage extraction for Qwen
        usage = {}
        if response.usage:
            usage = {
                'input_tokens': Decimal((response.usage.prompt_tokens) / 1000),
                'output_tokens': Decimal((response.usage.completion_tokens) / 1000),
            }

        return {'success': True, 'content': content, 'usage': usage}

    except Exception as e:
        return {'success': False, 'error': f'[LLM ERROR] {str(e)}'}
