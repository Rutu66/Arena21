from django.apps import AppConfig


class MainappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mainapp'
    
    
from django.apps import AppConfig

class YourAppConfig(AppConfig):
    name = 'mainapp'

    def ready(self):
        import mainapp.signal

