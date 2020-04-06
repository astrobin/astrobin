from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_notifications.utils import push_notification


class Command(BaseCommand):
    help = "Sends a notification to users with images lacking data."

    def handle(self, *args, **options):
        for user in User.objects.all():
            number = 0
            qs = Image.objects.filter(user=user, is_wip=False)

            number += qs.filter(
                (Q(subject_type=SubjectType.DEEP_SKY) & Q(subjects=None)) |
                (Q(subject_type=SubjectType.SOLAR_SYSTEM) & Q(solar_system_main_subject=None))).count()
            number += qs.filter(Q(imaging_telescopes=None) | Q(imaging_cameras=None)).count()
            number += qs.filter(Q(acquisition=None)).count()

            if number > 0:
                push_notification(
                    [user],
                    'lacking_data_reminder',
                    {'number': number,
                     'url': user.get_absolute_url() + '?public&sub=nodata'})
