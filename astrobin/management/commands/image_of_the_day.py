from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from astrobin.models import Image, Favorite, ImageOfTheDay
from astrobin.image_utils import make_image_of_the_day, make_runnerup
from nested_comments.models import NestedComment

from datetime import date, datetime, timedelta


def calculate_score(image):
    author = image.user
    votes = 0
    for vote in image.votes.all():
        votes += vote.score

    times_favorited = Favorite.objects.filter(image = image).exclude(user = author).count()
    comments = NestedComment.objects.filter(
        deleted = False,
        content_type__app_label = 'astrobin',
        content_type__model = 'image',
        object_id = image.id).exclude(author = author).count()

    score = votes + (times_favorited * 3) + (comments * 5)
    try:
        iotd = ImageOfTheDay.objects.get(image = image)
    except ImageOfTheDay.DoesNotExist:
        iotd = None

    if iotd:
        score = -1

    return score


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
                                                    Q(allow_rating = True) &
                                                    Q(user__userprofile__optout_rating = False) &
                                                    Q(w__gte = settings.IMAGE_OF_THE_DAY_WIDTH) &
                                                    Q(h__gte = settings.IMAGE_OF_THE_DAY_HEIGHT) &
                                                    Q(is_stored = True) &
                                                    Q(is_wip = False) &
                                                    Q(original_ext__in = ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']))
            start = start - timedelta(1)

        sorted_images = sorted(candidate_images, cmp = compare_images)

        print "IOTD: %d - %s (%d)" % (
            sorted_images[0].id, sorted_images[0].title.encode('utf-8'),
            calculate_score(sorted_images[0]))

        print "Runner up 1: %d - %s (%d)" % (
            sorted_images[1].id, sorted_images[1].title.encode('utf-8'),
            calculate_score(sorted_images[1]))

        print "Runner up 2: %d - %s (%d)" % (
            sorted_images[2].id, sorted_images[2].title.encode('utf-8'),
            calculate_score(sorted_images[2]))

        iotd = make_image_of_the_day(sorted_images[0])
        make_runnerup(sorted_images[1], iotd, 1)
        make_runnerup(sorted_images[2], iotd, 2)

