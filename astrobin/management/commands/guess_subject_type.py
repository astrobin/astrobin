from django.core.management.base import BaseCommand

from astrobin.enums import SubjectType
from astrobin.models import Image


class Command(BaseCommand):
    help = "Guesses subject type for images in which it's missing."

    def handle(self, *args, **options):
        images = Image.objects.filter(subject_type=None)
        for i in images:
            if i.solar_system_main_subject:
                i.subject_type = SubjectType.SOLAR_SYSTEM
            elif i.subjects:
                i.subject_type = SubjectType.DEEP_SKY
            else:
                i.subject_type = SubjectType.OTHER

            i.save(keep_deleted=True)

            print "Image %d: type %s." % (i.pk, i.subject_type)

        print "Processed %d images." % images.count()
