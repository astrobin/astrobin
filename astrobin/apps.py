# Django
from django.apps import AppConfig


class AstroBinAppConfig(AppConfig):
    name = 'astrobin'
    verbose_name = 'AstroBin'

    def ready(self):
        from astrobin.signals import *
        from astrobin_apps_notifications.signals import *
        from rawdata.signals import *
