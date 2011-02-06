from django.conf import settings

from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.s3.bucket import Bucket
from boto.exception import S3CreateError

import mimetypes
import email
import time
import datetime

from PIL import Image as PILImage
from PIL import ImageOps

import StringIO

from image_utils import *

def save_to_bucket(data, content_type, bucket, uid, ext):
    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    b = conn.create_bucket(bucket)
    k = Key(b)
    k.key = uid + ext
    k.set_metadata("Content-Type", content_type)

    headers = {}
    # HTTP/1.0
    headers['Expires'] = '%s GMT' % (email.Utils.formatdate(
        time.mktime((datetime.datetime.now() +
        datetime.timedelta(days=365*2)).timetuple())))
    # HTTP/1.1
    headers['Cache-Control'] = 'max-age %d' % (3600 * 24 * 365 * 2)

    k.set_contents_from_string(data, headers)
    k.set_acl("public-read");


def store_image_in_s3(path, uid, original_ext, mimetype=''):
    format_map = {'image/jpeg':('JPEG', '.jpg'),
                  'image/png' :('PNG', '.png'),
                 }

    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    content_type = mimetype if mimetype else mimetypes.guess_type(original_ext)[0]
    file = open(path + uid + original_ext)
    data = StringIO.StringIO(file.read())

    # First store the original image
    save_to_bucket(data.getvalue(), content_type, settings.S3_IMAGES_BUCKET, uid, original_ext)

    image = PILImage.open(data)
    # create histogram and store it
    histogram = generate_histogram(image)
    histogramFile = StringIO.StringIO()
    histogram.save(histogramFile, format_map['image/png'][0])
    save_to_bucket(histogramFile.getvalue(), 'image/png', settings.S3_HISTOGRAMS_BUCKET, uid, format_map['image/png'][1])

    # Then resize to the display image
    (w, h) = image.size
    (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
    resizedImage = image.resize((w, h), PILImage.ANTIALIAS)

    # Then save to bucket
    resizedFile = StringIO.StringIO()
    resizedImage.save(resizedFile, format_map[content_type][0])
    save_to_bucket(resizedFile.getvalue(), content_type, settings.S3_RESIZED_IMAGES_BUCKET, uid, format_map[content_type][1])

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
    save_to_bucket(thumbnailFile.getvalue(), 'image/png', settings.S3_THUMBNAILS_BUCKET, uid, format_map['image/png'][1])

    # Shrink more!
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.SMALL_THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # To the final bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, format_map[content_type][0])
    save_to_bucket(thumbnailFile.getvalue(), content_type, settings.S3_SMALL_THUMBNAILS_BUCKET, uid, format_map[content_type][1])

    # Let's also created a grayscale inverted image
    grayscale = ImageOps.grayscale(image)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, format_map[content_type][0])
    save_to_bucket(invertedFile.getvalue(), content_type, settings.S3_INVERTED_BUCKET, uid, format_map[content_type][1])
    grayscale = ImageOps.grayscale(resizedImage)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, format_map[content_type][0])
    save_to_bucket(invertedFile.getvalue(), content_type, settings.S3_RESIZED_INVERTED_BUCKET, uid, format_map[content_type][1])


def delete_image_from_s3(filename, ext):
    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    for bucket in ['astrobin_thumbnails',
                   'astrobin_small_thumbnails',
                   'astrobin_resized_inverted',
                   'astrobin_resized_image',
                   'astrobin_inverted',
                   'astrobin_images',
                   'astrobin_histograms',
                  ]:
        uid = filename
        if bucket == 'astrobin_thumbnails':
            uid += '.png'
        else:
            uid += ext

        b = Bucket(conn, bucket);
        k = Key(b)
        k.key = uid
        b.delete_key(k)

