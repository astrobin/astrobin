# Python
from time import sleep
import os

# Django
from django.core.management.base import BaseCommand
from django.utils.encoding import smart_unicode

# AstroBin
from astrobin.models import Image, ImageRevision

class Command(BaseCommand):
    help = "Adds missing 'size' attribute to Image/ImageRevision model instances"

    def handle(self, *args, **options):
        def patchSize(obj):
            name = smart_unicode(obj.image_file.name)
            path = name
            try:
                obj.size = obj.image_file.storage.size(path)
                obj.save(keep_deleted=True)
            except AttributeError:
                path = os.path.join('images', name)
                try:
                    obj.size = obj.image_file.storage.size(path)
                    obj.save(keep_deleted=True)
                except AttributeError as e:
                    print e

        qs = Image.all_objects.filter(size=0)
        i = 0
        total = qs.count()
        for image in qs:
            patchSize(image)
            i += 1
            for r in ImageRevision.all_objects.filter(image=image, size=0):
                patchSize(r)
            print "%d/%d" % (i, total)
            sleep(0.1)
