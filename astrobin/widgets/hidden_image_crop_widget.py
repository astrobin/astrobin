import logging

import image_cropping
from django.conf import settings
from easy_thumbnails.files import get_thumbnailer
from image_cropping.backends.easy_thumbs import EasyThumbnailsBackend
from image_cropping.widgets import HiddenImageCropWidget as BaseHiddenImageCropWidget

from astrobin.models import Image, ImageRevision

logger = logging.getLogger("apps")
_original_get_attrs = image_cropping.widgets.get_attrs

def _s3_get_attrs(image, name):
    _original = _original_get_attrs(image, name)

    if _original:
        return _original

    width, height = 0, 0

    try:
        astrobin_image = Image.all_objects.get(image_file=image)
        width, height = astrobin_image.w, astrobin_image.h
        url = astrobin_image.thumbnail('regular', None, sync=True)
        logger.info("Got URL %s: " % url)
    except Image.DoesNotExist:
        try:
            astrobin_image = ImageRevision.objects.get(image_file=image)
            width, height = astrobin_image.w, astrobin_image.h
            url = astrobin_image.thumbnail('regular', sync=True)
        except ImageRevision.DoesNotExist:
            return {}

    if width and height:
        return {
            'class': "crop-thumb",
            'data-thumbnail-url': url,
            'data-field-name': name,
            'data-org-width': width,
            'data-org-height': height,
            'data-max-width': width,
            'data-max-height': height,
        }

    logger.warning('Unable to generate image crop thumbnail due to image w/h being 0. Image: %d' % astrobin_image.pk)
    return {}


if settings.AWS_S3_ENABLED:
    image_cropping.widgets.get_attrs = _s3_get_attrs


class EasyThumbnailsBackend(EasyThumbnailsBackend):
    def get_thumbnail_url(self, path, thumbnail_options):
        try:
            target = Image.all_objects.get(image_file=path)
        except Image.DoesNotExist:
            try:
                target = ImageRevision.all_objects.get(image_file=path)
            except ImageRevision.DoesNotExist:
                return None

        thumb = get_thumbnailer(target.image_file.file, path)

        return thumb.get_thumbnail(settings.THUMBNAIL_ALIASES['']['regular']).url


class HiddenImageCropWidget(BaseHiddenImageCropWidget):
    def render(self, name, value, attrs=None):
        return super(BaseHiddenImageCropWidget, self).render(name, value, attrs)
