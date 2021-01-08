from django.core.management.base import BaseCommand

from astrobin.models import Image
from astrobin.utils import base26_encode


class Command(BaseCommand):
    help = "Fixes the ABC... labels of all revisions."

    def handle(self, *args, **options):
        images = Image.objects.exclude(imagerevision=None).order_by('id')
        for i in images:
            count = 0
            for r in i.imagerevision_set.all().order_by('id'):
                r.label = base26_encode(count)
                r.save(keep_deleted=True)
                count += 1

        print("Processed %d images." % images.count())
