from django.apps import AppConfig

class EgazAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'egaz_app'

    def ready(self):
        import egaz_app.signals  # <- this ensures signals are loaded
