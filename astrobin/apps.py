from PIL import Image, ImageOps
from PIL.ImageFile import ImageFile
from django.apps import AppConfig
from django.conf import settings

Image.MAX_IMAGE_PIXELS = 16536 * 16536
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

        self.init_actstream()
        self.init_avatar()
        self.init_search()
