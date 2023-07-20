# http://stackoverflow.com/questions/5877497/storing-images-and-thumbnails-on-s3-in-django
import logging
import os
import tempfile
from numbers import Number
from os.path import splitext

from django.conf import settings
from django.core.files.images import ImageFile, get_image_dimensions
from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


def _get_video_dimensions(file_or_path):
    if hasattr(file_or_path, 'read'):
        file = file_or_path
        file.seek(0)
    else:
        file = open(file_or_path, 'rb')

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        # Write the content of the file object to the temporary file
        temp.write(file.read())
        # Get the temporary file's path
        temp_path = temp.name

    # Load the video file
    clip = VideoFileClip(temp_path)
    # Get the size of the video
    video_size = clip.size
    # Close the clip
    clip.close()

    # Remove the temporary file
    os.unlink(temp_path)

    return video_size


def _get_image_dimensions(self):
    ext = splitext(self.file.name)[1].lower()

    if ext in settings.ALLOWED_VIDEO_EXTENSIONS:
        return _get_video_dimensions(self)

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
