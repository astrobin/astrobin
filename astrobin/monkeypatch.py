# http://stackoverflow.com/questions/5877497/storing-images-and-thumbnails-on-s3-in-django
import logging
from numbers import Number

from django.core.files.images import ImageFile
from django.core.files.images import get_image_dimensions

logger = logging.getLogger('apps')

def _get_image_dimensions(self):
    if not hasattr(self, '_dimensions_cache'):
        close = self.closed

        if self.field.width_field and self.field.height_field:
            width = getattr(self.instance, self.field.width_field)
            height = getattr(self.instance, self.field.height_field)

            # Check if the fields have proper values.
            if isinstance(width, Number) and isinstance(height, Number) and width > 0 and height > 0:
                self._dimensions_cache = (width, height)
            else:
                try:
                    self.open()
                    self._dimensions_cache = get_image_dimensions(self, close=close)
                except Exception as e:
                    logger.error("_get_image_dimensions: %s" % str(e))
                    self._dimensions_cache = 0, 0
        else:
            try:
                self.open()
                self._dimensions_cache = get_image_dimensions(self, close=close)
            except Exception as e:
                logger.error("_get_image_dimensions: %s" % str(e))
                self._dimensions_cache = 0, 0

    if self._dimensions_cache[0] == 0 or self._dimensions_cache[1] == 0:
        logger.error("_get_image_dimensions: got 0 width or height")

    return self._dimensions_cache


ImageFile._get_image_dimensions = _get_image_dimensions
