from datetime import datetime, timedelta, date

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Count

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote
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

        not_iotd = not self.is_iotd(image)
        has_promotions = \
            hasattr(image, 'iotdvote_set') and \
            image.iotdsubmission_set.count() > 0
        has_enough_promotions = \
            hasattr(image, 'iotdvote_set') and \
            image.iotdsubmission_set.count() >= settings.IOTD_REVIEW_MIN_PROMOTIONS
        published_before_multiple_promotions_requirement = \
            image.published and \
            image.published < settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START
        not_excluded = not image.user.userprofile.exclude_from_competitions
        published_within_window = \
            image.published and \
            image.published < datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)

        return \
            not_iotd and \
            (has_enough_promotions or (has_promotions and published_before_multiple_promotions_requirement)) and \
            not_excluded and \
            published_within_window

    def get_top_picks(self):
        return Image.objects.annotate(
            num_votes=Count('iotdvote')
        ).exclude(
            Q(corrupted=True) |
            Q(user__userprofile__exclude_from_competitions=True)
        ).filter(
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date())) &
            Q(
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                Q(published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
            )
        ).order_by('-published')

    def is_top_pick_nomination(self, image):
        # type: (Image) -> bool

        not_top_pick = not self.is_top_pick(image)
        has_promotions = \
            hasattr(image, 'iotdsubmission_set') and \
            image.iotdsubmission_set.count() > 0
        has_enough_promotions = \
            hasattr(image, 'iotdsubmission_set') and \
            image.iotdsubmission_set.count() >= settings.IOTD_SUBMISSION_MIN_PROMOTIONS
        published_before_multiple_promotions_requirement = \
            image.published and \
            image.published < settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START
        not_excluded = not image.user.userprofile.exclude_from_competitions
        published_within_window = \
            image.published and \
            image.published < datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)

        return \
            not_top_pick and \
            (has_enough_promotions or (has_promotions and published_before_multiple_promotions_requirement)) and \
            not_excluded and \
            published_within_window

    def get_top_pick_nominations(self):
        return Image.objects.annotate(
            num_submissions=Count('iotdsubmission')
        ).filter(
            Q(corrupted=False) &
            Q(iotdvote__isnull=True) &
            Q(
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                Q(published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
            ) &
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)) &
            Q(user__userprofile__exclude_from_competitions=False)
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
            Q(
                Q(moderator_decision=1) &
                Q(published__gte=datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)) &
                Q(designated_iotd_submitters=submitter)
            ) &
            ~Q(
                Q(user=submitter) |
                Q(subject_type__in=(SubjectType.GEAR, SubjectType.OTHER)) |
                Q(Q(iotdsubmission__submitter=submitter) & Q(iotdsubmission__date__lt=date.today())) |
                Q(iotddismissedimage__user=submitter)
            )
        ).order_by(
            '-published'
        )

        return [x for x in images if can_add(x)]

    def get_review_queue(self, reviewer):
        days = settings.IOTD_REVIEW_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        return sorted(list(set([
            x.image
            for x in IotdSubmission.objects.annotate(
                num_submissions=Count('image__iotdsubmission')
            ).filter(
                Q(date__gte=cutoff) &
                Q(image__designated_iotd_reviewers=reviewer) &
                Q(
                    Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                    Q(image__published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ).exclude(
                Q(submitter=reviewer) |
                Q(image__user=reviewer) |
                Q(image__iotddismissedimage__user=reviewer)
            )
            if (
                    not Iotd.objects.filter(
                        image=x.image,
                        date__lte=datetime.now().date()).exists()
                    and not IotdVote.objects.filter(
                reviewer=reviewer,
                image=x.image,
                date__lt=date.today()).exists()
            )
        ])), key=lambda x: x.published, reverse=True)

    def get_judgement_queue(self):
        days = settings.IOTD_JUDGEMENT_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        return sorted(list(set([
            x.image
            for x in IotdVote.objects.annotate(
                num_votes=Count('image__iotdvote')
            ).filter(
                Q(date__gte=cutoff) &
                Q(
                    Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                    Q(image__published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            )
            if not Iotd.objects.filter(
                image=x.image,
                date__lte=datetime.now().date()).exists()
        ])), key=lambda x: x.published, reverse=True)
