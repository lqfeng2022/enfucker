from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    # override ready(), is called when this app is ready, is initialized..
    def ready(self) -> None:
        import core.signals
