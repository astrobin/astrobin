import image_cropping
from django.conf import settings
from image_cropping.widgets import HiddenImageCropWidget as BaseHiddenImageCropWidget

from astrobin.models import Image, ImageRevision

_original_get_attrs = image_cropping.widgets.get_attrs

def _s3_get_attrs(image, name):
    _original = _original_get_attrs(image, name)

    if _original:
        return _original

    width, height = 0, 0

    try:
        astrobin_image = Image.all_objects.get(image_file=image)
        width, height = astrobin_image.w, astrobin_image.h
    except Image.DoesNotExist:
        try:
            astrobin_image = ImageRevision.objects.get(image_file=image)
            width, height = astrobin_image.w, astrobin_image.h
        except ImageRevision.DoesNotExist:
            return {}

    if width and height:
        return {
            'class': "crop-thumb",
            'data-thumbnail-url': astrobin_image.thumbnail_raw('regular').url,
            'data-field-name': name,
            'data-org-width': width,
            'data-org-height': height,
            'data-max-width': width,
            'data-max-height': height,
        }

    return {}


if settings.AWS_S3_ENABLED:
    image_cropping.widgets.get_attrs = _s3_get_attrs


class HiddenImageCropWidget(BaseHiddenImageCropWidget):
    def render(self, name, value, attrs=None):
        return super(BaseHiddenImageCropWidget, self).render(name, value, attrs)
