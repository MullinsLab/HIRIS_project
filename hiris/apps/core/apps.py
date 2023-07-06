from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hiris.apps.core'

    def ready(self):
        from hiris.apps.core import signals