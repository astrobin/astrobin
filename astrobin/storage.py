from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import mimetypes
import email
import time
import datetime

from PIL import Image as PILImage
from PIL import ImageOps

import StringIO

from image_utils import *

def save_to_bucket(filename, content):
    default_storage.save(filename, ContentFile(content));

def store_image_in_backend(path, uid, original_ext, mimetype=''):
    format_map = {'image/jpeg':('JPEG', '.jpg'),
                  'image/png' :('PNG', '.png'),
                 }

    content_type = mimetype if mimetype else mimetypes.guess_type(uid+original_ext)[0]
    file = open(path + uid + original_ext)
    data = StringIO.StringIO(file.read())

    # First store the original image
    save_to_bucket(uid + '' + original_ext, data.getvalue())

    image = PILImage.open(data)
    # create histogram and store it
    histogram = generate_histogram(image)
    histogramFile = StringIO.StringIO()
    histogram.save(histogramFile, format_map['image/png'][0])
    save_to_bucket(uid + '_hist.png', histogramFile.getvalue())

    # Then resize to the display image
    (w, h) = image.size
    (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
    resizedImage = image.resize((w, h), PILImage.ANTIALIAS)

    # Then save to bucket
    resizedFile = StringIO.StringIO()
    resizedImage.save(resizedFile, format_map[content_type][0])
    save_to_bucket(uid + '_resized' + format_map[content_type][1],
                   resizedFile.getvalue())

    # Then resize to the thumbnail
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # Then mask to rounded corners
    mask = PILImage.open('astrobin/thumbnail-mask.png').convert('L');
    output = ImageOps.fit(croppedImage, mask.size, centering=(0.5, 0.5))
    output.putalpha(mask)

    # Then save to bucket
    thumbnailFile = StringIO.StringIO()
    output.save(thumbnailFile, format_map['image/png'][0])
    save_to_bucket(uid + '_thumb.png', thumbnailFile.getvalue())

    # Shrink more!
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.SMALL_THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # To the final bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, format_map[content_type][0])
    save_to_bucket(uid + '_small_thumb' + format_map[content_type][1],
                   thumbnailFile.getvalue())

    # Let's also created a grayscale inverted image
    grayscale = ImageOps.grayscale(image)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, format_map[content_type][0])
    save_to_bucket(uid + '_inverted' + format_map[content_type][1],
                   invertedFile.getvalue())
    grayscale = ImageOps.grayscale(resizedImage)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, format_map[content_type][0])
    save_to_bucket(uid + '_resized_inverted' + format_map[content_type][1],
                   invertedFile.getvalue())


def delete_image_from_backend(filename, ext):
    for suffix in (
        '',
        '_hist',
        '_resized',
        '_thumb',
        '_small_thumb',
        '_inverted',
        '_resized_inverted',
    ):
        default_storage.delete(filename + ext);
