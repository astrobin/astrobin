from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models import Q

from astrobin.models import Image, Favorite, Comment, ImageOfTheDay
from astrobin.image_utils import crop_box_max, scale_dimensions
from astrobin.storage import save_to_bucket

from PIL import Image as PILImage
import os
import urllib2
import tempfile
import StringIO
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
                    if coolness > current_coolness:
                        coolest_image = image
                        current_coolness = coolness
                        print "Coolest image: [%s] [%d]" % (image.title, coolness)
            else:
                yesterday = yesterday - timedelta(1)

        tempdir = tempfile.mkdtemp()
        url = 'http://s3.amazonaws.com/astrobin_images/%s%s' \
              % (coolest_image.filename, coolest_image.original_ext)
        path = os.path.join(tempdir, coolest_image.filename + coolest_image.original_ext)

        try:
            print "Getting file from S3..."
            u = urllib2.urlopen(url)
        except:
            print coolest_image.filename + ": HTTP error."
            return

        print "Saving file..."
        f = open(path, 'w')
        f.write(u.read())
        f.close()

        print "Reading file..."
        f = open(path, 'r')
        image = PILImage.open(f)

        print "Resizing..."
        (w, h) = image.size
        (w, h) = scale_dimensions(w, h, settings.IMAGE_OF_THE_DAY_WIDTH)
        image = image.resize((w, h), PILImage.ANTIALIAS)
        (w, h) = image.size
        print "New size = (%d, %d)." % (w, h)

        print "Cropping..."
        (x1, y1, x2, y2) = crop_box_max(w, h,
                              settings.IMAGE_OF_THE_DAY_WIDTH,
                              settings.IMAGE_OF_THE_DAY_HEIGHT)

        print "Cropping to (%d, %d, %d, %d)..." % (x1, y1, x2, y2)
        image = image.crop((x1, y1, x2, y2))

        print "Dumping content..."
        f2 = StringIO.StringIO()
        image.save(f2, 'JPEG', quality=100)

        print "Saving to S3..."
        save_to_bucket(coolest_image.filename + '_iotd.jpg', f2.getvalue())
        
        print "Saving to database..."
        iotd = ImageOfTheDay(image = coolest_image)
        iotd.save()

        print "Cleaning up..."
        f.close()
        f2.close()
        os.remove(path)
        os.removedirs(tempdir)    

        print "Done."
