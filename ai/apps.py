from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'

    def ready(self) -> None:
        import ai.signals


# # Validate default models at startup
# def ready(self):
#     from ai.models import AIModel
#     for name in ('scribe_v1', 'eleven_v3', 'deepseek-chat'):
#         AIModel.objects.get(name=name)
