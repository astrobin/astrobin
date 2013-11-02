from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import mimetypes
import email
import time
import datetime
import os.path

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
    ttf = os.path.join(settings.STATIC_ROOT, 'fonts/arial.ttf')

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

