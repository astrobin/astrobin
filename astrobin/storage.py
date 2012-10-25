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
from PIL import ImageFont
from PIL import ImageDraw

import StringIO


def download_from_bucket(filename, path):
    import urllib2
    s3_path = '%s%s' % (settings.IMAGES_URL, filename)
    image = urllib2.urlopen(s3_path)
    output = open(path + filename, 'wb')
    output.write(image.read())
    output.flush()
    output.close()


def save_to_bucket(filename, content):
    default_storage.save('images/%s' % filename, ContentFile(content));


def watermark_image(image, text, position, opacity):
    watermark = PILImage.new('RGBA', (image.size[0], image.size[1]))
    draw = ImageDraw.Draw(watermark, 'RGBA')
    fontsize = 1
    ttf = 'sitestatic/fonts/arial.ttf'

    img_fraction = 0.33

    font = ImageFont.truetype(ttf, fontsize)
    while font.getsize(text)[0] < img_fraction*image.size[0]:
        # iterate until the text size is just larger than the criteria
        fontsize += 1
        font = ImageFont.truetype(ttf, fontsize)

    # de-increment to be sure it is less than criteria
    fontsize -= 1
    font = ImageFont.truetype(ttf, fontsize)

    if position == 0:
        pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
               image.size[1] * .5 - font.getsize(text)[1] * .5)
    elif position == 1:
        pos = (image.size[0] * .02,
               image.size[1] * .02)
    elif position == 2:
        pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
               image.size[1] * .02)
    elif position == 3:
        pos = (image.size[0] * .98 - font.getsize(text)[0],
               image.size[1] * .02)
    elif position == 4:
        pos = (image.size[0] * .02,
               image.size[1] * .98 - font.getsize(text)[1])
    elif position == 5:
        pos = (image.size[0] * .5 - font.getsize(text)[0] * .5,
               image.size[1] * .98 - font.getsize(text)[1])
    elif position == 6:
        pos = (image.size[0] * .98 - font.getsize(text)[0],
               image.size[1] * .98 - font.getsize(text)[1])

    draw.text(pos, text, font=font)
    mask = watermark.convert('L').point(lambda x: min(x, opacity))
    watermark.putalpha(mask)
    image.paste(watermark, None, watermark)

    return image


def store_image_in_backend(path, image_model):
    def fix_image_mode(im):
        if im.mode != "RGB" and im.mode != "I":
            im = im.convert("RGB")
        return im

    from image_utils import scale_dimensions_for_cropping, scale_dimensions,\
                            crop_box, crop_box_max, generate_histogram


    format_map = {'image/jpeg':('JPEG', '.jpg'),
                  'image/png' :('PNG', '.png'),
                  'image/gif' :('GIF', '.gif'),
                 }
    uid = image_model.filename
    original_ext = image_model.original_ext

    content_type = mimetypes.guess_type(uid+original_ext)[0]
    try:
        file = open(path + uid + original_ext)
    except IOError:
        return (0, 0, False)

    data = StringIO.StringIO(file.read())

    image = PILImage.open(data)

    is_animated = False
    if content_type == 'image/gif':
        try:
            image.seek(1)
            is_animated = True
        except:
            image.seek(0)
            is_animated = False


    try:
        image_model = image_model.image
    except AttributeError:
        pass
    if image_model.watermark and not is_animated:
        image = watermark_image(
            image,
            image_model.watermark_text,
            image_model.watermark_position,
            image_model.watermark_opacity)
        data = StringIO.StringIO()
        image.save(data, format_map[content_type][0], quality=100)
        image = fix_image_mode(image)

    save_to_bucket(uid + original_ext, data.getvalue())

    if not is_animated:
        try:
            # create histogram and store it
            histogram = generate_histogram(image)
            histogramFile = StringIO.StringIO()
            histogram.save(histogramFile, format_map['image/png'][0])
            save_to_bucket(uid + '_hist.png', histogramFile.getvalue())
        except:
            # I've seen this fail sometimes with IOError: image is truncated.
            pass

        # Then resize to the display image
        (w, h) = image.size
        (w, h) = scale_dimensions(w, h, settings.RESIZED_IMAGE_SIZE)
        resizedImage = image.resize((w, h), PILImage.ANTIALIAS)

        # Then save to bucket
        resizedFile = StringIO.StringIO()
        resizedImage = fix_image_mode(resizedImage)
        resizedImage.save(resizedFile, format_map[content_type][0], quality=100)
        save_to_bucket(uid + '_resized' + format_map[content_type][1],
                       resizedFile.getvalue())
        # Also, save this to uploads/ so the solver can pick it up
        resizedImage.save(path + uid + '_resized' + format_map[content_type][1],
                          format_map[content_type][0], quality=100)

        # Let's also created a grayscale inverted image
        grayscale = ImageOps.grayscale(image)
        inverted = ImageOps.invert(grayscale)
        enhancer = ImageEnhance.Contrast(inverted)
        inverted = enhancer.enhance(2.5)
        invertedFile = StringIO.StringIO()
        inverted = fix_image_mode(inverted)
        inverted.save(invertedFile, format_map[content_type][0])
        save_to_bucket(uid + '_inverted' + format_map[content_type][1],
                       invertedFile.getvalue())
        grayscale = ImageOps.grayscale(resizedImage)
        inverted = ImageOps.invert(grayscale)
        enhancer = ImageEnhance.Contrast(inverted)
        inverted = enhancer.enhance(2.5)
        invertedFile = StringIO.StringIO()
        inverted = inverted.convert("RGB")
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
    print croppedImage.mode
    croppedImage = fix_image_mode(croppedImage)
    croppedImage.save(thumbnailFile, format_map[content_type][0])
    save_to_bucket(uid + '_small_thumb' + format_map[content_type][1],
                   thumbnailFile.getvalue())

    return (image.size[0], image.size[1], is_animated)

def delete_image_from_backend(filename, ext):
    # Let's not really delete anything.
    """
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
    """
