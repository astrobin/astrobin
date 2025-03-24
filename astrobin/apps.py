from PIL import Image, ImageOps
from PIL.ImageFile import ImageFile
from django.apps import AppConfig
from django.conf import settings

from astrobin.monkeypatch import _get_primary_avatar

Image.MAX_IMAGE_PIXELS = 32768 * 32768
ImageFile.LOAD_TRUNCATED_IMAGES = True


class AstroBinAppConfig(AppConfig):
    name = 'astrobin'
    verbose_name = 'AstroBin'

    def init_avatar(self):
        from avatar.models import Avatar

        # See: https://github.com/grantmcconnaughey/django-avatar/issues/207
        def _transpose_image(self, image):
            orientation = 0x0112
            code = image.getexif().get(orientation, 1)
            if code and code != 1:
                image = ImageOps.exif_transpose(image)

            return image

        Avatar.transpose_image = _transpose_image

    def init_actstream(self):
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
        registry.register('astrobin_apps_equipment.equipmentitemmarketplacelisting')
        registry.register('astrobin_apps_equipment.telescope')
        registry.register('astrobin_apps_equipment.camera')
        registry.register('astrobin_apps_equipment.sensor')
        registry.register('astrobin_apps_equipment.mount')
        registry.register('astrobin_apps_equipment.filter')
        registry.register('astrobin_apps_equipment.software')
        registry.register('astrobin_apps_equipment.accessory')

    def init_search(self):
        from astrobin.search import set_max_result_window

        set_max_result_window(
            settings.HAYSTACK_CONNECTIONS['default']['INDEX_NAME'],
            1000000
        )

    def ready(self):
        from astrobin import signals  # noqa
        from astrobin_apps_notifications import signals  # noqa
        from astrobin.locale_extras import LOCALE_EXTRAS  # noqa
        from langdetect import DetectorFactory

        self.init_actstream()
        self.init_avatar()
        self.init_search()

        DetectorFactory.seed = 0

        import avatar.utils
        avatar.utils.get_primary_avatar = _get_primary_avatar

