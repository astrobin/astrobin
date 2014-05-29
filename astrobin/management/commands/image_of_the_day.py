from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from toggleproperties.models import ToggleProperty

from astrobin.models import Image, ImageOfTheDay
from astrobin.image_utils import make_image_of_the_day, make_runnerup, candidate_images_for_iotd

from datetime import date, datetime, timedelta


def calculate_score(image):
    try:
        iotd = ImageOfTheDay.objects.get(image = image)
        return -1
    except ImageOfTheDay.DoesNotExist:
        return ToggleProperty.objects.toggleproperties_for_object("like", image).count()


def compare_images(a, b):
    score_a = calculate_score(a)
    score_b = calculate_score(b)

    if score_a > score_b:
        return -1
    if score_a < score_b:
        return 1

    return 0


class Command(BaseCommand):
    help = "Calculates and saves the image of the day."

    def handle(self, *args, **options):
        coolest_image = None
        yesterday = date.today() - timedelta(1)
        start = yesterday - timedelta(7)

        candidate_images = []
        while not candidate_images:
            candidate_images = Image.objects.filter(Q(uploaded__gte = start) &
                                                    Q(uploaded__lte = yesterday) &
                                                    Q(subject_type__lt = 500) &
                                                    Q(w__gte = settings.THUMBNAIL_ALIASES['']['iotd']['size'][0]) &
                                                    Q(h__gte = settings.THUMBNAIL_ALIASES['']['iotd']['size'][1]) &
                                                    Q(is_wip = False))
            start = start - timedelta(1)

        sorted_images = sorted(candidate_images, cmp = compare_images)[:25]
        candidate_images_for_iotd(sorted_images)

