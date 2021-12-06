from datetime import datetime, timedelta, date
from typing import List

from django.conf import settings
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q, Count
from django.utils.translation import gettext

from astrobin.enums import SubjectType
from astrobin.models import Image
from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote, TopPickArchive, TopPickNominationsArchive
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
from common.services import DateTimeService


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
            Q(image__deleted__isnull=True))

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

    def get_submission_queue(self, submitter: User) -> List[Image]:
        def can_add(image: Image) -> bool:
            # Since the introduction of the 2020 plans, Free users cannot participate in the IOTD/TP.
            user_is_free: bool = is_free(image.user)

            return not user_is_free

        images = Image.objects \
            .annotate(
            num_dismissals=Count('iotddismissedimage', distinct=True)
        ) \
            .filter(
            Q(
                Q(moderator_decision=1) &
                Q(published__gte=datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)) &
                Q(designated_iotd_submitters=submitter) &
                Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS) &
                Q(
                    Q(iotd__isnull=True) |
                    Q(iotd__date__gt=datetime.now().date())
                )
            ) &
            ~Q(
                Q(user__userprofile__exclude_from_competitions=True) |
                Q(user=submitter) |
                Q(subject_type__in=(SubjectType.GEAR, SubjectType.OTHER)) |
                Q(
                    Q(iotdsubmission__submitter=submitter) &
                    Q(iotdsubmission__date__lt=date.today())
                ) |
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
                num_submissions=Count('image__iotdsubmission', distinct=True),
                num_dismissals=Count('image__iotddismissedimage', distinct=True)
            ).filter(
                Q(image__deleted__isnull=True),
                Q(date__gte=cutoff) &
                Q(image__designated_iotd_reviewers=reviewer) &
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) &
                Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS) &
                Q(
                    Q(image__iotd__isnull=True) |
                    Q(image__iotd__date__gt=datetime.now().date())
                )
            ).exclude(
                Q(submitter=reviewer) |
                Q(image__user=reviewer) |
                Q(image__iotddismissedimage__user=reviewer)
            )
            if not IotdVote.objects.filter(
                reviewer=reviewer,
                image=x.image,
                date__lt=date.today()
            ).exists()
        ])), key=lambda x: x.published, reverse=True)

    def get_judgement_queue(self):
        days = settings.IOTD_JUDGEMENT_WINDOW_DAYS
        cutoff = datetime.now() - timedelta(days)
        return sorted(list(set([
            x.image
            for x in IotdVote.objects.annotate(
                num_votes=Count('image__iotdvote', distinct=True),
                num_dismissals=Count('image__iotddismissedimage', distinct=True)
            ).filter(
                Q(image__deleted__isnull=True),
                Q(date__gte=cutoff) &
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) &
                Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS) &
                Q(
                    Q(image__iotd__isnull=True) |
                    Q(image__iotd__date__gt=datetime.now().date())
                )
            )
        ])), key=lambda x: x.published, reverse=True)

    def judge_cannot_select_now_reason(self, judge):
        # type: (User) -> Union[str, None]

        if Iotd.objects.filter(
                judge=judge,
                date=DateTimeService.today()).count() >= settings.IOTD_JUDGEMENT_MAX_PER_DAY:
            return gettext("you already selected %s IOTD today (UTC)" % settings.IOTD_JUDGEMENT_MAX_PER_DAY)

        if Iotd.objects.filter(
                judge=judge,
                date__gt=DateTimeService.today()).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE:
            return gettext("you already selected %s scheduled IOTDs" % settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE)

        if Iotd.objects.filter(date__gte=DateTimeService.today()).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS:
            return gettext("there are already %s scheduled IOTDs" % settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS)

        return None

    def get_next_available_selection_time_for_judge(self, judge):
        # type: (User) -> datetime

        today = DateTimeService.today()  # date
        now = DateTimeService.now()  # datetime

        next_time_due_to_max_per_day = \
            DateTimeService.next_midnight() if \
                Iotd.objects.filter(
                    judge=judge,
                    date=today).count() >= settings.IOTD_JUDGEMENT_MAX_PER_DAY \
                else now  # datetime

        latest_scheduled = Iotd.objects.filter(judge=judge).order_by('-date').first()  # Iotd
        next_time_due_to_max_scheduled_per_judge = \
            DateTimeService.next_midnight(latest_scheduled.date) if \
                Iotd.objects.filter(
                    judge=judge,
                    date__gt=today).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE \
                else now

        next_time_due_to_max_scheduled = \
            DateTimeService.next_midnight() if \
                Iotd.objects.filter(date__gte=today).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS \
                else now

        return max(
            next_time_due_to_max_per_day,
            next_time_due_to_max_scheduled_per_judge,
            next_time_due_to_max_scheduled
        )

    def update_top_pick_nomination_archive(self):
        latest = TopPickNominationsArchive.objects.first()

        items = Image.objects.annotate(
            num_submissions=Count('iotdsubmission', distinct=True)
        ).filter(
            Q(
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                Q(
                    Q(num_submissions__gt=0) &
                    Q(published__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            Q(published__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS))
        ).order_by('-published')

        if latest:
            items = items.filter(published__gt=latest.image.published)

        for item in items.iterator():
            try:
                TopPickNominationsArchive.objects.create(image=item)
            except IntegrityError:
                continue

    def update_top_pick_archive(self):
        latest = TopPickArchive.objects.first()

        items = Image.objects.annotate(
            num_votes=Count('iotdvote', distinct=True)
        ).filter(
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

        if latest:
            items = items.filter(published__gt=latest.image.published)

        for item in items.iterator():
            try:
                TopPickArchive.objects.create(image=item)
            except IntegrityError:
                continue

    def get_inactive_submitter_and_reviewers(self, days):
        inactive_members = []
        members = User.objects.filter(groups__name__in=['iotd_submitters', 'iotd_reviewers'])

        for member in members.iterator():
            if member.is_superuser:
                continue

            if 'iotd_reviewers' in member.groups.all().values_list('name', flat=True):
                actions = IotdVote.objects.filter(reviewer=member).order_by('-date')
                action_count = actions.count()
                last_action = actions.first().date if action_count > 0 else None
            elif 'iotd_submitters' in member.groups.all().values_list('name', flat=True):
                actions = IotdSubmission.objects.filter(submitter=member).order_by('-date')
                action_count = actions.count()
                last_action = actions.first().date if action_count > 0 else None
            else:
                continue

            if last_action is None or last_action.date() == DateTimeService.today() - timedelta(days=days):
                inactive_members.append(member)

        return inactive_members
