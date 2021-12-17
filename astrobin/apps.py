from PIL import Image
from django.apps import AppConfig

Image.MAX_IMAGE_PIXELS = 16536 * 16536


class AstroBinAppConfig(AppConfig):
    name = 'astrobin'
    verbose_name = 'AstroBin'

    def registerActStreamModels(self):
        from actstream import registry
        registry.register('auth.user')
        registry.register('astrobin.gear')
        registry.register('astrobin.telescope')
        registry.register('astrobin.camera')
        registry.register('astrobin.mount')
        registry.register('astrobin.filter')
        registry.register('astrobin.software')
        registry.register('astrobin.accessory')
        registry.register('astrobin.focalreducer')
        registry.register('astrobin.image')
        registry.register('astrobin.imagerevision')
        registry.register('nested_comments.nestedcomment')
        registry.register('toggleproperties.toggleproperty')
        registry.register('astrobin_apps_groups.group')

    def ready(self):
        from astrobin import signals  # noqa
        from astrobin_apps_notifications import signals  # noqa
        from astrobin.locale_extras import LOCALE_EXTRAS  # noqa

        self.registerActStreamModels()
