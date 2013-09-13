from django.conf import settings

from astrobin.storage import save_to_bucket

from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageDraw

import os
import urllib2
import tempfile
import StringIO
from datetime import datetime


def make_image_of_the_day(image):
    from astrobin.models import Image, ImageRevision, ImageOfTheDay

    today = datetime.now().date()
    try:
        iotd = ImageOfTheDay.objects.get(date = today)
        iotd.image = image
    except ImageOfTheDay.DoesNotExist:
        iotd = ImageOfTheDay(image = image)

    iotd.save()
    return iotd


def make_runnerup(image, iotd, position):
    if position == 1:
        iotd.runnerup_1 = image
    elif position == 2:
        iotd.runnerup_2 = image

    iotd.save()
