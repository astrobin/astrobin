# -*- coding: utf-8 -*-


from django.apps import AppConfig


class AstrobinAppsIotdConfig(AppConfig):
    name = 'astrobin_apps_iotd'

    def ready(self):
        import astrobin_apps_iotd.signals  # noqa
