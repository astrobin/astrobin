from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from astrobin.models import Image, Favorite, Comment
from astrobin.image_utils import make_image_of_the_day

from datetime import date, datetime, timedelta

class Command(BaseCommand):
    help = "Calculates and saves the image of the day."

    def handle(self, *args, **options):
        coolest_image = None
        yesterday = date.today() - timedelta(1)

        while coolest_image is None:
            print yesterday

            yesterdays_images = Image.objects.filter(Q(uploaded__gte = yesterday) &
                                                     Q(uploaded__lt = date.today()) &
                                                     Q(w__gte = settings.IMAGE_OF_THE_DAY_WIDTH) &
                                                     Q(h__gte = settings.IMAGE_OF_THE_DAY_HEIGHT) &
                                                     Q(is_stored = True) &
                                                     Q(is_wip = False))

            if yesterdays_images:
                coolest_image = yesterdays_images[0]
                current_coolness = 0
                for image in yesterdays_images:
                    score = 0
                    for vote in image.votes.all():
                        score += vote.score 

                    times_favorited = Favorite.objects.filter(image = image).count()
                    comments = Comment.objects.filter(image = image).count()

                    coolness = score + (times_favorited * 3) + (comments * 5)

                    print "Examining: [%s] [%d/%d]" % (image.title.encode('utf-8'), coolness, current_coolness)
                    if coolness > current_coolness:
                        coolest_image = image
                        current_coolness = coolness
                        print "\tCoolest image: [%s] [%d]" % (image.title.encode('utf-8'), coolness)
            else:
                yesterday = yesterday - timedelta(1)

        make_image_of_the_day(coolest_image)

