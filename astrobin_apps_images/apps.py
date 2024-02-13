# -*- coding: utf-8 -*-


from django.apps import AppConfig


class AstrobinAppsImagesConfig(AppConfig):
    name = 'astrobin_apps_images'

    def ready(self):
        import astrobin_apps_images.signals  # noqa
