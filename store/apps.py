from django.apps import AppConfig


# Auto-syncs when Django starts
class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'

    def ready(self) -> None:
        import store.signals
