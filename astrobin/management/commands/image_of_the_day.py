from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from astrobin.models import Image, Favorite, ImageOfTheDay
from astrobin.image_utils import make_image_of_the_day
from nested_comments.models import NestedComment

from datetime import date, datetime, timedelta

class Command(BaseCommand):
    help = "Calculates and saves the image of the day."

    def handle(self, *args, **options):
        coolest_image = None
        yesterday = date.today() - timedelta(1)
        day_before_yesterday = yesterday - timedelta(1)

        while coolest_image is None:
            print day_before_yesterday

            candidate_images = Image.objects.filter(Q(uploaded__gte = day_before_yesterday) &
                                                    Q(uploaded__lt = yesterday) &
                                                    Q(subject_type__lt = 500) &
                                                    Q(allow_rating = True) &
                                                    Q(user__userprofile__optout_rating = False) &
                                                    Q(w__gte = settings.IMAGE_OF_THE_DAY_WIDTH) &
                                                    Q(h__gte = settings.IMAGE_OF_THE_DAY_HEIGHT) &
                                                    Q(is_stored = True) &
                                                    Q(is_wip = False) &
                                                    Q(original_ext__in = ['.jpg', '.jpeg', '.JPG', '.JPEG', '.png', '.PNG']))

            if candidate_images:
                coolest_image = candidate_images[0]
                current_coolness = 0
                for image in candidate_images:
                    author = image.user
                    score = 0
                    for vote in image.votes.all():
                        score += vote.score

                    times_favorited = Favorite.objects.filter(image = image).count()
                    comments = NestedComment.objects.filter(
                        deleted = False,
                        content_type__app_label = 'astrobin',
                        content_type__model = 'image',
                        object_id = image.id).exclude(author = author).count()

                    coolness = score + (times_favorited * 3) + (comments * 5)
                    try:
                        iotd = ImageOfTheDay.objects.get(image = image)
                    except ImageOfTheDay.DoesNotExist:
                        iotd = None
                    if iotd:
                        coolness = -1

                    print "Examining: [%s] [%d/%d]" % (image.title.encode('utf-8'), coolness, current_coolness)
                    if coolness > current_coolness:
                        coolest_image = image
                        current_coolness = coolness
                        print "\tCoolest image: [%s] [%d]" % (image.title.encode('utf-8'), coolness)
            else:
                day_before_yesterday = day_before_yesterday - timedelta(1)

        make_image_of_the_day(coolest_image)

