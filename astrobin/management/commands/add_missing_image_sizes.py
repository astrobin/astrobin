# Python
import os

# Django
from django.core.management.base import BaseCommand

# AstroBin
from astrobin.models import Image, ImageRevision

class Command(BaseCommand):
    help = "Adds missing 'size' attribute to Image/ImageRevision model instances"

    def handle(self, *args, **options):
        def patchSize(obj):
            try:
                obj.size = obj.image_file.storage.size(
                    os.path.join('images', obj.image_file.name)
                )
                obj.save()
            except AttributeError:
                print "\tSkipped due to error"

        for image in Image.all_objects.filter(size=0):
            print "Patching image: \n\t- %s\n\t- %s\n\t- %s" % (
                image.title,
                image.user.username,
                image.image_file.name)
            patchSize(image)

            for r in ImageRevision.all_objects.filter(image=image, size=0):
                print "\t\t- Revision %s" % r.label
                patchSize(r)
