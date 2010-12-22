from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings

import mimetypes
from uuid import uuid4
from PIL import Image as PILImage
from PIL import ImageOps
import StringIO

from models import Image

def store_image_in_s3(file, uid, mimetype=''):
    def scale_dimensions(w, h, longest_side):
        if w > longest_side:
            ratio = longest_side*1./w
        elif h > longest_side:
            ratio = longest_side*1./h
        else:
            ratio = 1

        return (int(w*ratio), int(h*ratio))

    def scale_dimensions_for_cropping(w, h, shortest_side):
        if w < shortest_side and h < shortest_side:
            return (w, h)
        if w > h:
            ratio = shortest_side*1./h
        else:
            ratio = shortest_side*1./w

        return (int(w*ratio), int(h*ratio))

    def crop_box(w, h):
        if w > h:
            return ((w-h)/2, 0, (w+h)/2, h)
        elif h > w:
            return (0, (h-w)/2, w, (h+w)/2)
        return (0, 0, w, h)

    def save_to_bucket(data, content_type, bucket, uid):
        b = conn.create_bucket(bucket)
        k = Key(b)
        k.key = uid
        k.set_metadata("Content-Type", content_type)
        k.set_contents_from_string(data)
        k.set_acl("public-read");

    conn = S3Connection(settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY)
    content_type = mimetype if mimetype else mimetypes.guess_type(file.name)[0]
    data = StringIO.StringIO(file.read())

    # First store the original image
    save_to_bucket(data.getvalue(), content_type, settings.S3_IMAGES_BUCKET, uid)

    # Then resize to the display image
    image = PILImage.open(data)
    (w, h) = image.size
    (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
    resizedImage = image.resize((w, h), PILImage.ANTIALIAS)

    # Then save to bucket
    resizedFile = StringIO.StringIO()
    resizedImage.save(resizedFile, 'JPEG')
    save_to_bucket(resizedFile.getvalue(), 'image/jpeg', settings.S3_RESIZED_IMAGES_BUCKET, uid)

    # Then resize to the thumbnail
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # Then save to bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, 'JPEG')
    save_to_bucket(thumbnailFile.getvalue(), 'image/jpeg', settings.S3_THUMBNAILS_BUCKET, uid)

    # Shrink more!
    (w, h) = image.size
    (w, h) = scale_dimensions_for_cropping(w, h, settings.SMALL_THUMBNAIL_SIZE)
    thumbnailImage = image.resize((w, h), PILImage.ANTIALIAS)
    croppedImage = thumbnailImage.crop(crop_box(w, h))

    # To the final bucket
    thumbnailFile = StringIO.StringIO()
    croppedImage.save(thumbnailFile, 'JPEG')
    save_to_bucket(thumbnailFile.getvalue(), 'image/jpeg', settings.S3_SMALL_THUMBNAILS_BUCKET, uid)

    # Let's also created a grayscale inverted image
    grayscale = ImageOps.grayscale(image)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, 'JPEG')
    save_to_bucket(invertedFile.getvalue(), 'image/jpeg', settings.S3_INVERTED_BUCKET, uid)

    # Then we invert the resized image too
    grayscale = ImageOps.grayscale(resizedImage)
    inverted = ImageOps.invert(grayscale)
    invertedFile = StringIO.StringIO()
    inverted.save(invertedFile, 'JPEG')
    save_to_bucket(invertedFile.getvalue(), 'image/jpeg', settings.S3_RESIZED_INVERTED_BUCKET, uid)

