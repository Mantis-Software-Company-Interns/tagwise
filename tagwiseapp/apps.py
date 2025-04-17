from django.apps import AppConfig


class TagwiseappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tagwiseapp'
    
    def ready(self):
        """Import signals when the app is ready"""
        from . import signals
