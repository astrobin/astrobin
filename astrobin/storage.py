from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import mimetypes
import email
import time
import datetime

from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageEnhance

import StringIO

from image_utils import *


def download_from_bucket(filename, path):
    import urllib2
    s3_path = 'http://astrobin_images.%s/%s' % (settings.S3_URL, filename)
    image = urllib2.urlopen(s3_path)
    output = open(path + filename, 'wb')
    output.write(image.read())
    output.flush()
    output.close()

def save_to_bucket(filename, content):
    default_storage.save(filename, ContentFile(content));

def store_image_in_backend(path, uid, original_ext, mimetype=''):
    format_map = {'image/jpeg':('JPEG', '.jpg'),
                  'image/png' :('PNG', '.png'),
                  'image/gif' :('GIF', '.gif'),
                 }

    content_type = mimetype if mimetype else mimetypes.guess_type(uid+original_ext)[0]
    try:
        file = open(path + uid + original_ext)
    except IOError:
        return (0, 0, False)

    data = StringIO.StringIO(file.read())

    # First store the original image
    save_to_bucket(uid + '' + original_ext, data.getvalue())

    image = PILImage.open(data)

    is_animated = False
    if content_type == 'image/gif':
        try:
            image.seek(1)
            is_animated = True
        except:
            image.seek(0)
            is_animated = False

    if not is_animated:
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
        resizedImage.save(resizedFile, format_map[content_type][0], quality=100)
        save_to_bucket(uid + '_resized' + format_map[content_type][1],
                       resizedFile.getvalue())
        # Also, save this to uploads/ so can the solver can pick it up
        resizedImage.save(path + uid + '_resized' + format_map[content_type][1],
                          format_map[content_type][0], quality=100)

        # Let's also created a grayscale inverted image
        grayscale = ImageOps.grayscale(image)
        inverted = ImageOps.invert(grayscale)
        enhancer = ImageEnhance.Contrast(inverted)
        inverted = enhancer.enhance(2.5)
        invertedFile = StringIO.StringIO()
        inverted.save(invertedFile, format_map[content_type][0])
        save_to_bucket(uid + '_inverted' + format_map[content_type][1],
                       invertedFile.getvalue())
        grayscale = ImageOps.grayscale(resizedImage)
        inverted = ImageOps.invert(grayscale)
        enhancer = ImageEnhance.Contrast(inverted)
        inverted = enhancer.enhance(2.5)
        invertedFile = StringIO.StringIO()
        inverted.save(invertedFile, format_map[content_type][0])
        save_to_bucket(uid + '_resized_inverted' + format_map[content_type][1],
                       invertedFile.getvalue())
    else:
        save_to_bucket(uid + '_resized' + format_map[content_type][1],
                       data.getvalue())

    # Then resize to the thumbnail
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # Then mask to rounded corners
    mask = PILImage.open('astrobin/thumbnail-mask.png').convert('L');
    output = ImageOps.fit(croppedImage, mask.size, centering=(0.5, 0.5))
    try:
        output.putalpha(mask)
    except ValueError:
        pass

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

    return (image.size[0], image.size[1], is_animated)

def delete_image_from_backend(filename, ext):
    for suffix in (
        '',
        '_resized',
        '_small_thumb',
        '_inverted',
        '_resized_inverted',
        '_solved',
    ):
        whole_name = filename + suffix + ext
        print "Deleting %s." % whole_name
        default_storage.delete(whole_name)

    for suffix in (
        '_thumb',
        '_hist',
    ):
        whole_name = filename + suffix + '.png'
        print "Deleting %s." % whole_name
        default_storage.delete(whole_name)

