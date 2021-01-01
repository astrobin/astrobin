from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


class IotdService:
    def get_iotds(self):
        return Iotd.objects \
            .filter(date__lte=datetime.now().date(), image__deleted=None) \
            .exclude(image__corrupted=True)

    def get_top_picks(self):
        return Image.objects.exclude(Q(iotdvote=None) | Q(corrupted=True)).filter(
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date()))
        ).order_by('-published')

    def get_top_pick_nominations(self):
        return Image.objects.filter(
            corrupted=False,
            iotdvote__isnull=True,
            iotdsubmission__isnull=False,
            published__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)
        ).order_by('-published').distinct()

    def get_submission_queue(self, submitter):
        # type: (User) -> list[Image]

        def can_add(image):
            # type: (Image) -> bool

            # Since the introduction of the 2020 plans, Free users cannot participate in the IOTD/TP.
            user_is_free = is_free(image.user)  # type: bool
            already_iotd = Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists()  # type: bool

            return not user_is_free and not already_iotd

        images = Image.objects.exclude(
            user=submitter
        ).filter(
            moderator_decision=1,
            published__gte=datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS),
            designated_iotd_submitters=submitter
        ).exclude(
            subject_type__in=(SubjectType.GEAR, SubjectType.OTHER)
        ).order_by(
            '-published'
        )

        return [x for x in images if can_add(x)]
