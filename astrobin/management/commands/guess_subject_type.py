from django.core.management.base import BaseCommand

from astrobin.models import Image

class Command(BaseCommand):
    help = "Guesses subject type for images in which it's missing."

    def handle(self, *args, **options):
        images = Image.objects.filter(subject_type = None)
        for i in images:
            if i.solar_system_main_subject:
                i.subject_type = 200
            elif i.subjects:
                i.subject_type = 100
            else:
                i.subject_type = 600

            i.save(keep_deleted=True)

            print "Image %d: type %d." % (i.pk, i.subject_type)

        print "Processed %d images." % images.count()
