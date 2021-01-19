from datetime import datetime, timedelta, date

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Count

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote, TopPickArchive, TopPickNominationsArchive
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
        return Iotd.objects.filter(
            Q(date__lte=datetime.now().date()) &
            Q(image__deleted__isnull=True) &
            ~Q(image__corrupted=True))

    def is_top_pick(self, image):
        # type: (Image) -> bool
        return TopPickArchive.objects.filter(image=image).exists() and \
               image.user.userprofile.exclude_from_competitions != True

    def get_top_picks(self):
        return TopPickArchive.objects.all()

    def is_top_pick_nomination(self, image):
        # type: (Image) -> bool
        return TopPickNominationsArchive.objects.filter(image=image).exists() and \
               image.user.userprofile.exclude_from_competitions != True

    def get_top_pick_nominations(self):
        return TopPickNominationsArchive.objects.all()

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
                Q(user__userprofile__exclude_from_competitions=True) |
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
                num_submissions=Count('image__iotdsubmission', distinct=True)
            ).filter(
                Q(date__gte=cutoff) &
                Q(image__designated_iotd_reviewers=reviewer) &
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS)
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
                num_votes=Count('image__iotdvote', distinct=True)
            ).filter(
                Q(date__gte=cutoff) &
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS)
            )
            if not Iotd.objects.filter(
                image=x.image,
                date__lte=datetime.now().date()).exists()
        ])), key=lambda x: x.published, reverse=True)

    def update_top_pick_nomination_archive(self):
        TopPickNominationsArchive.objects.all().delete()

        items = Image.objects.annotate(
            num_submissions=Count('iotdsubmission', distinct=True)
        ).filter(
            ~Q(corrupted=True) &
            Q(iotdvote__isnull=True) &
            Q(
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                Q(
                    Q(num_submissions__gt=0) &
                    Q(published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS))
        ).order_by('-published').distinct()

        for item in items:
            TopPickNominationsArchive.objects.create(image=item)

    def update_top_pick_archive(self):
        TopPickArchive.objects.all().delete()

        items = Image.objects.annotate(
            num_votes=Count('iotdvote', distinct=True)
        ).filter(
            ~Q(corrupted=True) &
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date())) &
            Q(
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                Q(
                    Q(num_votes__gt=0) &
                    Q(published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            )
        ).order_by('-published')

        for item in items:
            TopPickArchive.objects.create(image=item)
