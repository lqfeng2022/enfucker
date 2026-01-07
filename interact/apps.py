from django.apps import AppConfig


class InteractConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interact'

    # override ready(), is called when this app is ready, is initialized..
    def ready(self) -> None:
        import interact.signals
