# http://stackoverflow.com/questions/5877497/storing-images-and-thumbnails-on-s3-in-django
import json
import logging
import os
import subprocess
import tempfile
from numbers import Number
from os.path import splitext

from django.conf import settings
from django.core.files.images import ImageFile, get_image_dimensions

logger = logging.getLogger(__name__)


def _get_video_dimensions(file_or_path):
    def get_video_metadata(path):
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,display_aspect_ratio,sample_aspect_ratio:stream_tags=rotate',
            '-of', 'json',
            path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        metadata = json.loads(result.stdout.decode('utf-8'))
        logger.debug(result.stdout.decode('utf-8'))
        return metadata

    # Handle file or file path input
    if hasattr(file_or_path, 'read'):
        file = file_or_path
        file.seek(0)
    else:
        file = open(file_or_path, 'rb')

    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(file.read())
        temp_path = temp.name

    # Get video metadata
    metadata = get_video_metadata(temp_path)
    width = metadata['streams'][0].get('width')
    height = metadata['streams'][0].get('height')
    tags = metadata['streams'][0].get('tags', {})
    rotation = int(tags.get('rotate', 0))  # Default to 0 if no rotate tag

    # Check for SAR and adjust width accordingly
    sar = metadata['streams'][0].get('sample_aspect_ratio')
    if sar and sar != '1:1':
        sar_num, sar_den = map(int, sar.split(':'))
        width = int(width * sar_num / sar_den)

    # If no rotate tag, check display_aspect_ratio (DAR) as a fallback
    if rotation == 0:
        display_aspect_ratio = metadata['streams'][0].get('display_aspect_ratio')
        if display_aspect_ratio:
            dar_width, dar_height = map(int, display_aspect_ratio.split(":"))
            # Check if DAR orientation doesn't match pixel dimension orientation
            dar_is_portrait = dar_height > dar_width
            pixels_are_portrait = height > width
            if dar_is_portrait != pixels_are_portrait:
                width, height = height, width

    # Adjust dimensions if rotation is 90 or 270 degrees
    if rotation in (90, 270):
        width, height = height, width

    # Cleanup temporary file
    os.unlink(temp_path)

    return width, height


def _get_image_dimensions(self):
    try:
        ext = splitext(self.file.name)[1].lower()
    except FileNotFoundError:
        return 0, 0

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


def _get_primary_avatar(user, size: settings.AVATAR_DEFAULT_SIZE):
    from astrobin_apps_users.services import UserService
    service = UserService(user)
    return service.get_primary_avatar(size)
