from django.conf import settings

from astrobin.models import ImageOfTheDay
from toggleproperties.models import ToggleProperty

from PIL import Image as PILImage
from PIL import ImageOps
from PIL import ImageDraw

import os
import urllib2
import tempfile
import StringIO
from datetime import datetime


def compare_images(a, b):
    def calculate_score(image):
        try:
            iotd = ImageOfTheDay.objects.get(image = image)
            return -1
        except ImageOfTheDay.DoesNotExist:
            return image.likes()

    score_a = calculate_score(a)
    score_b = calculate_score(b)

    if score_a > score_b:
        return -1
    if score_a < score_b:
        return 1

    return 0


def compare_iotd_candidates(a, b):
    return compare_images(a.image, b.image)


def candidate_images_for_iotd(images):
    from astrobin.models import ImageOfTheDayCandidate

    for position, i in enumerate(images):
        # Generate the thumbnail so that images are not slow to load when they
        # are presented for selection.
        i.thumbnail('iotd_candidate')
        c = ImageOfTheDayCandidate.objects.create(image = i, position = position)


def make_image_of_the_day(image, user):
    from astrobin.models import Image, ImageRevision, ImageOfTheDay

    today = datetime.now().date()
    try:
        iotd = ImageOfTheDay.objects.get(date = today)
        iotd.image = image
    except ImageOfTheDay.DoesNotExist:
        iotd = ImageOfTheDay(image = image)

    iotd.chosen_by = user
    iotd.save()
    return iotd


def make_runnerup(image, iotd, position):
    if position == 1:
        iotd.runnerup_1 = image
    elif position == 2:
        iotd.runnerup_2 = image

    iotd.save()
