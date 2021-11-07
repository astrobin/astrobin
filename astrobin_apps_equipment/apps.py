# -*- coding: utf-8 -*-


from django.apps import AppConfig


class AstrobinAppsEquipmentConfig(AppConfig):
    name = 'astrobin_apps_equipment'

    def ready(self):
        import astrobin_apps_equipment.signals # noqa
