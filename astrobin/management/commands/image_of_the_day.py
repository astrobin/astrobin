from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from toggleproperties.models import ToggleProperty

from astrobin.models import Image, ImageOfTheDay
from astrobin.image_utils import candidate_images_for_iotd

from datetime import date, datetime, timedelta
from random import shuffle


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
    help = "Selects candidates for the Image of the Day."

    def handle(self, *args, **options):
        liked_images = []
        random_images = []

        start = date.today() - timedelta(8) # A week before yesterday
        end = date.today() - timedelta(1)   # Yesterday

        query = {
            'start': Q(uploaded__gte = start),
            'end'  : Q(uploaded__lte = end),
            'type' : Q(subject_type__lt = 500),
            'w'    : Q(w__gte = settings.THUMBNAIL_ALIASES['']['iotd']['size'][0]),
            'h'    : Q(h__gte = settings.THUMBNAIL_ALIASES['']['iotd']['size'][1]),
            'wip'  : Q(is_wip = False),
        }

        # First let's get some of the most liked images during the past 7 days.
        while not liked_images:
            liked_images = list(Image.objects.filter(reduce(lambda x, y: x & y, query.values())))
            start = start - timedelta(1)
            query['start'] = Q(uploaded__gte = start)
        liked_images = sorted(liked_images, cmp = compare_images)[:25]

        # Then let's get some random ones too.
        start = date.today() - timedelta(8)
        query['start'] = Q(uploaded__gte = start)
        while not random_images:
            random_images = list(Image.objects.filter(reduce(lambda x, y: x & y, query.values())).order_by('?')[:25])
            start = start - timedelta(1)
            query['start'] = Q(uploaded__gte = start)

        # Now remove duplicates and shuffle everything
        candidates = list(set(liked_images + random_images))
        shuffle(candidates)

        candidate_images_for_iotd(candidates)
