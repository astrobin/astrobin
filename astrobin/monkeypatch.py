# http://stackoverflow.com/questions/5877497/storing-images-and-thumbnails-on-s3-in-django
from django.core.files.images import ImageFile
def _get_image_dimensions(self):
    from numbers import Number
    if not hasattr(self, '_dimensions_cache'):
        close = self.closed
        if self.field.width_field and self.field.height_field:
            width = getattr(self.instance, self.field.width_field)
            height = getattr(self.instance, self.field.height_field)
            #check if the fields have proper values
            if isinstance(width, Number) and isinstance(height, Number):
                self._dimensions_cache = (width, height)
            else:
                self.open()
                self._dimensions_cache = get_image_dimensions(self, close=close)
        else:
            self.open()
            self._dimensions_cache = get_image_dimensions(self, close=close)

    return self._dimensions_cache
ImageFile._get_image_dimensions = _get_image_dimensions
