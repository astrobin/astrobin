from datetime import datetime, timedelta, date

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdSubmission
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free


class IotdService:
    def is_iotd(self, image):
        # type: (Image) -> bool
        return \
            hasattr(image, 'iotd') and \
            image.iotd is not None and \
            image.iotd.date <= datetime.now().date() and \
            not image.user.userprofile.exclude_from_competitions

    def get_iotds(self):
        return Iotd.objects \
            .filter(date__lte=datetime.now().date(), image__deleted=None,
                    image__user__userprofile__exclude_from_competitions=False) \
            .exclude(image__corrupted=True)

    def is_top_pick(self, image):
        # type: (Image) -> bool
        return \
            (not hasattr(image, 'iotd') or image.iotd.date > datetime.now().date()) and \
            hasattr(image, 'iotdvote_set') and \
            image.iotdvote_set.count() > 0 and \
            not image.user.userprofile.exclude_from_competitions and \
            image.published < datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)

    def get_top_picks(self):
        return Image.objects.exclude(
            Q(iotdvote=None) | Q(corrupted=True) |
            Q(user__userprofile__exclude_from_competitions=True)
        ).filter(
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date()))
        ).order_by('-published')

    def is_top_pick_nomination(self, image):
        # type: (Image) -> bool
        return \
            (not hasattr(image, 'iotd') or image.iotd.date > datetime.now().date()) and \
            (not hasattr(image, 'iotdvote_set') or image.iotdvote_set.count() == 0) and \
            hasattr(image, 'iotdsubmission_set') and \
            image.iotdsubmission_set.count() > 0 and \
            not image.user.userprofile.exclude_from_competitions and \
            image.published < datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)

    def get_top_pick_nominations(self):
        return Image.objects.filter(
            corrupted=False,
            iotdvote__isnull=True,
            iotdsubmission__isnull=False,
            published__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS),
            user__userprofile__exclude_from_competitions=False
        ).order_by('-published').distinct()

    def get_submission_queue(self, submitter):
        # type: (User) -> list[Image]

        def can_add(image):
            # type: (Image) -> bool

            # Since the introduction of the 2020 plans, Free users cannot participate in the IOTD/TP.
            user_is_free = is_free(image.user)  # type: bool
            already_iotd = Iotd.objects.filter(image=image, date__lte=datetime.now().date()).exists()  # type: bool

            return not user_is_free and not already_iotd

        images = Image.objects \
            .filter(
            moderator_decision=1,
            published__gte=datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS),
            designated_iotd_submitters=submitter) \
            .exclude(
            Q(user=submitter) |
            Q(subject_type__in=(SubjectType.GEAR, SubjectType.OTHER)) |
            Q(Q(iotdsubmission__submitter=submitter) & Q(iotdsubmission__date__lt=date.today()))
        ).order_by(
            '-published'
        )

        return [x for x in images if can_add(x)]

    def get_review_queue(self, reviewer):
        days = settings.IOTD_REVIEW_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        return sorted(list(set([
            x.image
            for x in IotdSubmission.objects
                .filter(date__gte=cutoff, image__designated_iotd_reviewers=reviewer)
                .exclude(Q(submitter=reviewer) | Q(image__user=reviewer))
            if not Iotd.objects.filter(
                image=x.image,
                date__lte=datetime.now().date()).exists()
        ])), key=lambda x: x.published, reverse=True)
