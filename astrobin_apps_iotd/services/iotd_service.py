import logging
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Union

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db.models import Count, OuterRef, Prefetch, Q, QuerySet, Subquery
from django.utils import timezone
from django.utils.translation import gettext

from astrobin.enums import SubjectType
from astrobin.enums.data_source import DataSource
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdJudgementQueueEntry, IotdQueueSortOrder, IotdReviewQueueEntry,
    IotdStaffMemberScore, IotdStaffMemberSettings, IotdStats,
    IotdSubmission,
    IotdSubmissionQueueEntry, IotdSubmitterSeenImage, IotdVote,
    TopPickArchive,
    TopPickNominationsArchive,
)
from astrobin_apps_iotd.types.may_not_submit_to_iotd_tp_reason import MayNotSubmitToIotdTpReason
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from astrobin_apps_premium.services.premium_service import PremiumService
from astrobin_apps_premium.templatetags.astrobin_apps_premium_tags import is_free
from astrobin_apps_users.services import UserService
from common.constants import GroupName
from common.services import DateTimeService

log = logging.getLogger(__name__)


class IotdService:
    def is_iotd(self, image: Image) -> bool:
        return \
                hasattr(image, 'iotd') and \
                image.iotd is not None and \
                image.iotd.date <= datetime.now().date() and \
                not image.user.userprofile.exclude_from_competitions

    def is_future_iotd(self, image: Image) -> bool:
        profile = image.user.userprofile
        return \
                hasattr(image, 'iotd') and \
                image.iotd is not None and \
                image.iotd.date > datetime.now().date() and \
                not profile.exclude_from_competitions and \
                (profile.banned_from_competitions is None or
                 profile.banned_from_competitions > image.submitted_for_iotd_tp_consideration)

    def get_iotds(self) -> QuerySet:
        return Iotd.objects.filter(
            Q(date__lte=datetime.now().date()) &
            Q(image__deleted__isnull=True)
        )

    def is_top_pick(self, image: Image) -> bool:
        profile = image.user.userprofile
        return TopPickArchive.objects.filter(image=image).exists() and \
            profile.exclude_from_competitions is not True and \
            (profile.banned_from_competitions is None or
             profile.banned_from_competitions > image.submitted_for_iotd_tp_consideration)

    def get_top_picks(self) -> QuerySet:
        return TopPickArchive.objects.all()

    def is_top_pick_nomination(self, image: Image) -> bool:
        profile = image.user.userprofile
        return TopPickNominationsArchive.objects.filter(image=image).exists() and \
            profile.exclude_from_competitions is not True and \
            (profile.banned_from_competitions is None or
             profile.banned_from_competitions > image.submitted_for_iotd_tp_consideration)

    def get_top_pick_nominations(self) -> QuerySet:
        return TopPickNominationsArchive.objects.all()

    def get_submission_queue(self, submitter: User, queue_sort_order: str = None) -> List[IotdSubmissionQueueEntry]:
        member_settings: IotdStaffMemberSettings
        member_settings, created = IotdStaffMemberSettings.objects.get_or_create(user=submitter)
        queue_sort_order_before = member_settings.queue_sort_order

        if queue_sort_order in ('newest', 'oldest'):
            member_settings.queue_sort_order = IotdQueueSortOrder.NEWEST_FIRST \
                if queue_sort_order == 'newest' \
                else IotdQueueSortOrder.OLDEST_FIRST

        if member_settings.queue_sort_order != queue_sort_order_before:
            member_settings.save()

        order_by = [
            '-published'
            if member_settings.queue_sort_order == IotdQueueSortOrder.NEWEST_FIRST
            else 'published'
        ]

        images: List[IotdSubmissionQueueEntry] = []

        for entry in IotdSubmissionQueueEntry.objects.select_related(
            'image'
        ).prefetch_related(
            'image__imaging_telescopes_2', 'image__imaging_cameras_2'
        ).filter(
            submitter=submitter,
            image__submitted_for_iotd_tp_consideration__gte=DateTimeService.now() - timedelta(
                settings.IOTD_SUBMISSION_WINDOW_DAYS
            )
        ).order_by(
            *order_by
        ).iterator():
            image = entry.image
            final_revision = ImageService(image).get_final_revision()
            image.w = final_revision.w
            image.h = final_revision.h
            images.append(image)

        return images

    def get_review_queue(self, reviewer: User, queue_sort_order: str = None) -> List[IotdReviewQueueEntry]:
        member_settings: IotdStaffMemberSettings
        member_settings, created = IotdStaffMemberSettings.objects.get_or_create(user=reviewer)
        queue_sort_order_before = member_settings.queue_sort_order

        if queue_sort_order in ('newest', 'oldest'):
            member_settings.queue_sort_order = IotdQueueSortOrder.NEWEST_FIRST \
                if queue_sort_order == 'newest' \
                else IotdQueueSortOrder.OLDEST_FIRST

        if member_settings.queue_sort_order != queue_sort_order_before:
            member_settings.save()

        order_by = [
            '-last_submission_timestamp'
            if member_settings.queue_sort_order == IotdQueueSortOrder.NEWEST_FIRST
            else 'last_submission_timestamp'
        ]

        images: List[IotdReviewQueueEntry] = []

        for entry in IotdReviewQueueEntry.objects.select_related(
            'image'
        ).prefetch_related(
            'image__imaging_telescopes_2', 'image__imaging_cameras_2'
        ).filter(
            reviewer=reviewer,
            last_submission_timestamp__gte=DateTimeService.now() - timedelta(
                settings.IOTD_REVIEW_WINDOW_DAYS
            )
        ).order_by(
            *order_by
        ).iterator():
            image = entry.image
            image.last_submission_timestamp = entry.last_submission_timestamp
            images.append(image)

        return images

    def get_judgement_queue(self, judge: User, queue_sort_order: str = None) -> List[IotdJudgementQueueEntry]:
        member_settings: IotdStaffMemberSettings
        member_settings, created = IotdStaffMemberSettings.objects.get_or_create(user=judge)
        queue_sort_order_before = member_settings.queue_sort_order

        if queue_sort_order in ('newest', 'oldest'):
            member_settings.queue_sort_order = IotdQueueSortOrder.NEWEST_FIRST \
                if queue_sort_order == 'newest' \
                else IotdQueueSortOrder.OLDEST_FIRST

        if member_settings.queue_sort_order != queue_sort_order_before:
            member_settings.save()

        order_by = [
            '-last_vote_timestamp'
            if member_settings.queue_sort_order == IotdQueueSortOrder.NEWEST_FIRST
            else 'last_vote_timestamp'
        ]

        images: List[IotdJudgementQueueEntry] = []

        for entry in IotdJudgementQueueEntry.objects.select_related(
            'image'
        ).prefetch_related(
            'image__imaging_telescopes_2', 'image__imaging_cameras_2'
        ).filter(
            judge=judge,
            last_vote_timestamp__gte=DateTimeService.now() - timedelta(
                settings.IOTD_JUDGEMENT_WINDOW_DAYS
            )
        ).order_by(
            *order_by
        ).iterator():
            image = entry.image
            image.last_vote_timestamp = entry.last_vote_timestamp
            images.append(image)

        return images

    def judge_cannot_select_now_reason(self, judge):
        # type: (User) -> Union[str, None]

        if Iotd.objects.filter(
                judge=judge,
                created__date=DateTimeService.today()
        ).count() >= settings.IOTD_JUDGEMENT_MAX_PER_DAY:
            return gettext("you already selected %s IOTD(s) today (UTC)" % settings.IOTD_JUDGEMENT_MAX_PER_DAY)

        if Iotd.objects.filter(
                judge=judge,
                date__gt=DateTimeService.today()
        ).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE:
            return gettext("you already selected %s scheduled IOTD(s)" % settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE)

        if Iotd.objects.filter(date__gt=DateTimeService.today()).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS:
            return gettext("there are already %s scheduled IOTD(s)" % settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS)

        return None

    def get_next_available_selection_time_for_judge(self, judge):
        # type: (User) -> datetime

        today = DateTimeService.today()  # date
        now = DateTimeService.now()  # datetime

        next_time_due_to_max_per_day = \
            DateTimeService.next_midnight() if \
                Iotd.objects.filter(
                    judge=judge,
                    created__date=today
                ).count() >= settings.IOTD_JUDGEMENT_MAX_PER_DAY \
                else now  # datetime

        latest_scheduled = Iotd.objects.filter(judge=judge).order_by('-date').first()  # Iotd
        next_time_due_to_max_scheduled_per_judge = \
            DateTimeService.next_midnight(latest_scheduled.date) if \
                Iotd.objects.filter(
                    judge=judge,
                    date__gt=today
                ).count() >= settings.IOTD_JUDGEMENT_MAX_FUTURE_PER_JUDGE \
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
        items = Image.objects.annotate(
            num_submissions=Count('iotdsubmission', distinct=True),
            num_votes=Count('iotdvote', distinct=True)
        ).filter(
            Q(disqualified_from_iotd_tp__isnull=True) &
            Q(
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                Q(
                    Q(num_submissions__gt=0) &
                    Q(submitted_for_iotd_tp_consideration__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            ~Q(
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                Q(
                    Q(num_votes__gt=0) &
                    Q(submitted_for_iotd_tp_consideration__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            Q(
                submitted_for_iotd_tp_consideration__lt=datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
                )
            ) &
            Q(
                submitted_for_iotd_tp_consideration__gt=datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS + settings.IOTD_REVIEW_WINDOW_DAYS
                ) * 2
            ) &
            Q(toppicknominationsarchive__isnull=True)
        ).order_by('-submitted_for_iotd_tp_consideration')

        items.update(updated=DateTimeService.now())

        for item in items.iterator():
            TopPickNominationsArchive.objects.get_or_create(image=item)
            ImageService(item).clear_badges_cache()


    def update_top_pick_archive(self):
        items = Image.objects.annotate(
            num_votes=Count('iotdvote', distinct=True)
        ).filter(
            Q(disqualified_from_iotd_tp__isnull=True) &
            Q(
                submitted_for_iotd_tp_consideration__lt=datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS +
                    settings.IOTD_REVIEW_WINDOW_DAYS +
                    settings.IOTD_JUDGEMENT_WINDOW_DAYS
                )
            ) &
            Q(
                submitted_for_iotd_tp_consideration__gt=datetime.now() - timedelta(
                    settings.IOTD_SUBMISSION_WINDOW_DAYS +
                    settings.IOTD_REVIEW_WINDOW_DAYS +
                    settings.IOTD_JUDGEMENT_WINDOW_DAYS
                ) * 2
            ) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date())) &
            Q(
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                Q(
                    Q(num_votes__gt=0) &
                    Q(submitted_for_iotd_tp_consideration__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            Q(toppickarchive__isnull=True)
        ).order_by('-submitted_for_iotd_tp_consideration')

        items.update(updated=DateTimeService.now())

        for item in items.iterator():
            TopPickArchive.objects.get_or_create(image=item)
            ImageService(item).clear_badges_cache()

    def update_submission_queues(self):
        def _compute_queue(submitter: User):
            days = settings.IOTD_SUBMISSION_WINDOW_DAYS
            cutoff = datetime.now() - timedelta(days)

            return Image.objects \
                .annotate(
                num_dismissals=Count('iotddismissedimage', distinct=True),
            ) \
                .filter(
                Q(
                    Q(disqualified_from_iotd_tp__isnull=True) &
                    Q(moderator_decision=ModeratorDecision.APPROVED) &
                    Q(submitted_for_iotd_tp_consideration__gte=cutoff) &
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
                    Q(collaborators=submitter) |
                    Q(subject_type__in=(SubjectType.GEAR, SubjectType.OTHER)) |
                    Q(
                        Q(iotdsubmission__submitter=submitter) &
                        Q(iotdsubmission__date__lt=date.today())
                    ) |
                    Q(iotddismissedimage__user=submitter)
                )
            )

        for submitter in User.objects.filter(groups__name=GroupName.IOTD_SUBMITTERS):
            IotdSubmissionQueueEntry.objects.filter(submitter=submitter).delete()
            for image in _compute_queue(submitter).iterator():
                IotdSubmissionQueueEntry.objects.create(
                    submitter=submitter,
                    image=image,
                    published=image.submitted_for_iotd_tp_consideration
                )
                ImageService(image).clear_badges_cache()
                log.debug(
                    f'Image {image.get_id()} "{image.title}" assigned to submitter {submitter.pk} "{submitter.username}".'
                )

    def update_review_queues(self):
        def _compute_queue(reviewer: User):
            days = settings.IOTD_REVIEW_WINDOW_DAYS
            cutoff = datetime.now() - timedelta(days)

            return Image.objects.annotate(
                num_submissions=Count('iotdsubmission', distinct=True),
                num_dismissals=Count('iotddismissedimage', distinct=True),
                last_submission_timestamp=Subquery(IotdSubmission.last_for_image(OuterRef('pk')).values('date'))
            ).filter(
                Q(deleted__isnull=True) &
                Q(disqualified_from_iotd_tp__isnull=True) &
                Q(last_submission_timestamp__gte=cutoff) &
                Q(designated_iotd_reviewers=reviewer) &
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) &
                Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS) &
                Q(
                    Q(iotd__isnull=True) |
                    Q(iotd__date__gt=datetime.now().date())
                )
            ).exclude(
                Q(iotdsubmission__submitter=reviewer) |
                Q(user=reviewer) |
                Q(collaborators=reviewer) |
                Q(iotddismissedimage__user=reviewer) |
                Q(
                    Q(iotdvote__reviewer=reviewer) &
                    Q(iotdvote__date__lt=DateTimeService.today())
                )
            )

        for reviewer in User.objects.filter(groups__name=GroupName.IOTD_REVIEWERS):
            IotdReviewQueueEntry.objects.filter(reviewer=reviewer).delete()
            for image in _compute_queue(reviewer).iterator():
                last_submission = IotdSubmission.last_for_image(image.pk).first()
                IotdReviewQueueEntry.objects.create(
                    reviewer=reviewer,
                    image=image,
                    last_submission_timestamp=last_submission.date
                )
                ImageService(image).clear_badges_cache()
                log.debug(
                    f'Image {image.get_id()} "{image.title}" assigned to reviewer {reviewer.pk} "{reviewer.username}".'
                )

    def update_judgement_queues(self):
        def _compute_queue(judge: User):
            days = settings.IOTD_JUDGEMENT_WINDOW_DAYS
            cutoff = datetime.now() - timedelta(days)

            return Image.objects.annotate(
                num_votes=Count('iotdvote', distinct=True),
                num_dismissals=Count('iotddismissedimage', distinct=True),
                last_vote_timestamp=Subquery(IotdVote.last_for_image(OuterRef('pk')).values('date'))
            ).filter(
                Q(deleted__isnull=True) &
                Q(disqualified_from_iotd_tp__isnull=True) &
                Q(last_vote_timestamp__gte=cutoff) &
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) &
                Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS) &
                Q(
                    Q(iotd__isnull=True) |
                    Q(iotd__date__gt=datetime.now().date())
                )
            ).exclude(
                Q(iotdvote__reviewer=judge) |
                Q(iotddismissedimage__user=judge) |
                Q(user=judge) |
                Q(collaborators=judge)
            )

        for judge in User.objects.filter(groups__name=GroupName.IOTD_JUDGES):
            IotdJudgementQueueEntry.objects.filter(judge=judge).delete()
            for image in _compute_queue(judge).iterator():
                last_vote = IotdVote.last_for_image(image.pk).first()
                IotdJudgementQueueEntry.objects.create(
                    judge=judge,
                    image=image,
                    last_vote_timestamp=last_vote.date
                )
                ImageService(image).clear_badges_cache()
                log.debug(
                    f'Image {image.get_id()} "{image.title}" assigned to judge {judge.pk} "{judge.username}".'
                )

    def clear_stale_queue_entries(self):
        IotdSubmissionQueueEntry.objects.exclude(submitter__groups__name=GroupName.IOTD_SUBMITTERS).delete()
        IotdReviewQueueEntry.objects.exclude(reviewer__groups__name=GroupName.IOTD_REVIEWERS).delete()
        IotdJudgementQueueEntry.objects.exclude(judge__groups__name=GroupName.IOTD_JUDGES).delete()

    def get_insufficiently_active_submitters_and_reviewers(self):
        insufficiently_active_members = []
        members = User.objects.filter(groups__name__in=[GroupName.IOTD_SUBMITTERS, GroupName.IOTD_REVIEWERS])
        min_promotions_per_period = getattr(settings, 'IOTD_MIN_PROMOTIONS_PER_PERIOD', '7/7')
        min_promotions = int(min_promotions_per_period.split('/')[0])
        days = int(min_promotions_per_period.split('/')[1])
        cutoff = DateTimeService.now() - timedelta(days=days)

        for member in members.iterator():
            if member.is_superuser:
                continue

            if GroupName.IOTD_REVIEWERS in member.groups.all().values_list('name', flat=True):
                actions = IotdVote.objects.filter(reviewer=member, date__gte=cutoff)
                promotion_count = actions.count()
            elif GroupName.IOTD_SUBMITTERS in member.groups.all().values_list('name', flat=True):
                actions = IotdSubmission.objects.filter(submitter=member, date__gte=cutoff)
                promotion_count = actions.count()
            else:
                continue

            if promotion_count < min_promotions:
                insufficiently_active_members.append(member)

        return insufficiently_active_members

    def get_inactive_submitters_and_reviewers(self, days):
        inactive_members = []
        members = User.objects.filter(groups__name__in=[GroupName.IOTD_SUBMITTERS, GroupName.IOTD_REVIEWERS])

        for member in members.iterator():
            if member.is_superuser:
                continue

            if GroupName.IOTD_REVIEWERS in member.groups.all().values_list('name', flat=True):
                actions = IotdVote.objects.filter(reviewer=member).order_by('-date')
                action_count = actions.count()
                last_action = actions.first().date if action_count > 0 else None
            elif GroupName.IOTD_SUBMITTERS in member.groups.all().values_list('name', flat=True):
                actions = IotdSubmission.objects.filter(submitter=member).order_by('-date')
                action_count = actions.count()
                last_action = actions.first().date if action_count > 0 else None
            else:
                continue

            if last_action is None or last_action.date() == DateTimeService.today() - timedelta(days=days):
                inactive_members.append(member)

        return inactive_members

    @staticmethod
    def submit_to_iotd_tp_process(user: User, image: Image, auto_submit=False, agreed=False):
        may, reason = IotdService.may_submit_to_iotd_tp_process(user, image, agreed)

        if may:
            image.designated_iotd_submitters.add(
                *UserService.get_users_in_group_sample(
                    GroupName.IOTD_SUBMITTERS, settings.IOTD_DESIGNATED_SUBMITTERS_PERCENTAGE, image.user
                )
            )

            image.designated_iotd_reviewers.add(
                *UserService.get_users_in_group_sample(
                    GroupName.IOTD_REVIEWERS, settings.IOTD_DESIGNATED_REVIEWERS_PERCENTAGE, image.user
                )
            )

            for alias in ('story', 'hd_anonymized', 'hd_anonymized_crop', 'real_anonymized'):
                image.thumbnail(alias, 'final')

            Image.objects_including_wip.filter(pk=image.pk).update(submitted_for_iotd_tp_consideration=timezone.now())

            save = False
            if auto_submit:
                image.user.userprofile.auto_submit_to_iotd_tp_process = True
                save = True

            if agreed:
                image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines = DateTimeService.now()
                save = True

            if save:
                image.user.userprofile.save(keep_deleted=True)

            thumb = image.thumbnail_raw('gallery', None, sync=True)
            push_notification(
                [image.user], None, 'image_submitted_to_iotd_tp', {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None
                }
            )

        return may, reason

    @staticmethod
    def resubmit_to_iotd_tp_process(user: User, image: Image):
        log.debug(f'Resubmitting image {image.get_id()} "{image.title}" to IOTD/TP process.')

        group: Group = Group.objects.get(name=GroupName.IOTD_SUBMITTERS)
        previous_submitters: QuerySet = image.designated_iotd_submitters.all()
        new_submitters = [x for x in group.user_set.all() if x not in previous_submitters and x != user]

        image.designated_iotd_submitters.clear()
        image.designated_iotd_submitters.add(*new_submitters)

        Image.objects_including_wip.filter(pk=image.pk).update(submitted_for_iotd_tp_consideration=timezone.now())

    @staticmethod
    def may_submit_to_iotd_tp_process(user: User, image: Image, agreed=False):
        if not user.is_authenticated:
            return False, MayNotSubmitToIotdTpReason.NOT_AUTHENTICATED

        if user != image.user:
            return False, MayNotSubmitToIotdTpReason.NOT_OWNER

        if image.submitted_for_iotd_tp_consideration is not None:
            return False, MayNotSubmitToIotdTpReason.ALREADY_SUBMITTED

        if image.disqualified_from_iotd_tp is not None:
            return False, MayNotSubmitToIotdTpReason.DISQUALIFIED

        if image.published and image.published < (
                DateTimeService.now() - timedelta(days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS)
        ):
            return False, MayNotSubmitToIotdTpReason.TOO_LATE

        if is_free(PremiumService(user).get_valid_usersubscription()):
            return False, MayNotSubmitToIotdTpReason.IS_FREE

        if image.is_wip:
            return False, MayNotSubmitToIotdTpReason.NOT_PUBLISHED

        if image.subject_type in (SubjectType.GEAR, SubjectType.OTHER, '', None):
            return False, MayNotSubmitToIotdTpReason.BAD_SUBJECT_TYPE

        if image.imaging_telescopes_2.count() == 0 or image.imaging_cameras_2.count() == 0:
            return False, MayNotSubmitToIotdTpReason.NO_TELESCOPE_OR_CAMERA

        if image.acquisition_set.count() == 0 and image.subject_type in (
                SubjectType.DEEP_SKY,
                SubjectType.SOLAR_SYSTEM,
                SubjectType.WIDE_FIELD,
                SubjectType.STAR_TRAILS,
                SubjectType.LANDSCAPE,
        ):
            return False, MayNotSubmitToIotdTpReason.NO_ACQUISITIONS

        if image.user.userprofile.exclude_from_competitions:
            return False, MayNotSubmitToIotdTpReason.EXCLUDED_FROM_COMPETITIONS

        if image.user.userprofile.banned_from_competitions:
            return False, MayNotSubmitToIotdTpReason.BANNED_FROM_COMPETITIONS

        if (image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines is None or \
            image.user.userprofile.agreed_to_iotd_tp_rules_and_guidelines < settings.IOTD_LAST_RULES_UPDATE) and \
                not agreed:
            return False, MayNotSubmitToIotdTpReason.DID_NOT_AGREE_TO_RULES_AND_GUIDELINES

        return True, None

    @staticmethod
    def update_stats(days=365):
        cutoff = date.today() - timedelta(days=days)

        total_submitted_images_queryset = Image.objects \
            .filter(
            published__gt=cutoff, submitted_for_iotd_tp_consideration__isnull=False, subject_type__in=[
                SubjectType.DEEP_SKY,
                SubjectType.SOLAR_SYSTEM,
                SubjectType.WIDE_FIELD,
                SubjectType.STAR_TRAILS,
                SubjectType.NORTHERN_LIGHTS,
                SubjectType.NOCTILUCENT_CLOUDS,
                SubjectType.LANDSCAPE,
            ]
        )

        IotdStats.objects.create(
            # Period of time covered by the stats.
            days=days,

            # Distinct winners.
            distinct_iotd_winners=Iotd.objects \
                .filter(date__gt=cutoff) \
                .values_list('image__user', flat=True) \
                .distinct() \
                .count(),
            distinct_tp_winners=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .values_list('image__user', flat=True) \
                .distinct() \
                .count(),
            distinct_tpn_winners=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .values_list('image__user', flat=True) \
                .distinct() \
                .count(),

            # Total awarded images.
            total_iotds=days,
            total_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .count(),
            total_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .count(),

            # Total submitted images.
            total_submitted_images=total_submitted_images_queryset
                .count(),

            # Breakdown by subject type.
            total_deep_sky_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.DEEP_SKY) \
                .count(),
            total_solar_system_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.SOLAR_SYSTEM) \
                .count(),
            total_wide_field_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.WIDE_FIELD) \
                .count(),
            total_star_trails_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.STAR_TRAILS) \
                .count(),
            total_northern_lights_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.NORTHERN_LIGHTS) \
                .count(),
            total_noctilucent_clouds_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.NOCTILUCENT_CLOUDS) \
                .count(),
            total_landscape_images=total_submitted_images_queryset \
                .filter(subject_type=SubjectType.LANDSCAPE) \
                .count(),

            deep_sky_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.DEEP_SKY) \
                .count(),
            solar_system_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.SOLAR_SYSTEM) \
                .count(),
            wide_field_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.WIDE_FIELD) \
                .count(),
            star_trails_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.STAR_TRAILS) \
                .count(),
            northern_lights_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NORTHERN_LIGHTS) \
                .count(),
            noctilucent_clouds_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NOCTILUCENT_CLOUDS) \
                .count(),
            landscape_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__subject_type=SubjectType.LANDSCAPE) \
                .count(),

            deep_sky_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.DEEP_SKY) \
                .count(),
            solar_system_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.SOLAR_SYSTEM) \
                .count(),
            wide_field_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.WIDE_FIELD) \
                .count(),
            star_trails_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.STAR_TRAILS) \
                .count(),
            northern_lights_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NORTHERN_LIGHTS) \
                .count(),
            noctilucent_clouds_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NOCTILUCENT_CLOUDS) \
                .count(),
            landscape_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.LANDSCAPE) \
                .count(),

            deep_sky_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.DEEP_SKY) \
                .count(),
            solar_system_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.SOLAR_SYSTEM) \
                .count(),
            wide_field_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.WIDE_FIELD) \
                .count(),
            star_trails_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.STAR_TRAILS) \
                .count(),
            northern_lights_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NORTHERN_LIGHTS) \
                .count(),
            noctilucent_clouds_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.NOCTILUCENT_CLOUDS) \
                .count(),
            landscape_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__subject_type=SubjectType.LANDSCAPE) \
                .count(),

            # Breakdown by data source.
            total_backyard_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.BACKYARD) \
                .count(),
            total_traveller_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.TRAVELLER) \
                .count(),
            total_own_remote_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.OWN_REMOTE) \
                .count(),
            total_amateur_hosting_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.AMATEUR_HOSTING) \
                .count(),
            total_public_amateur_data_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.PUBLIC_AMATEUR_DATA) \
                .count(),
            total_pro_data_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.PRO_DATA) \
                .count(),
            total_mix_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.MIX) \
                .count(),
            total_other_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.OTHER) \
                .count(),
            total_unknown_images=total_submitted_images_queryset \
                .filter(data_source=DataSource.UNKNOWN) \
                .count(),

            backyard_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.BACKYARD) \
                .count(),
            traveller_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.TRAVELLER) \
                .count(),
            own_remote_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.OWN_REMOTE) \
                .count(),
            amateur_hosting_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.AMATEUR_HOSTING) \
                .count(),
            public_amateur_data_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.PUBLIC_AMATEUR_DATA) \
                .count(),
            pro_data_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.PRO_DATA) \
                .count(),
            mix_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.MIX) \
                .count(),
            other_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.OTHER) \
                .count(),
            unknown_iotds=Iotd.objects \
                .filter(date__gt=cutoff) \
                .filter(image__data_source=DataSource.UNKNOWN) \
                .count(),

            backyard_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.BACKYARD) \
                .count(),
            traveller_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.TRAVELLER) \
                .count(),
            own_remote_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.OWN_REMOTE) \
                .count(),
            amateur_hosting_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.AMATEUR_HOSTING) \
                .count(),
            public_amateur_data_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.PUBLIC_AMATEUR_DATA) \
                .count(),
            pro_data_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.PRO_DATA) \
                .count(),
            mix_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.MIX) \
                .count(),
            other_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.OTHER) \
                .count(),
            unknown_tps=TopPickArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.UNKNOWN) \
                .count(),

            backyard_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.BACKYARD) \
                .count(),
            traveller_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.TRAVELLER) \
                .count(),
            own_remote_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.OWN_REMOTE) \
                .count(),
            amateur_hosting_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.AMATEUR_HOSTING) \
                .count(),
            public_amateur_data_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.PUBLIC_AMATEUR_DATA) \
                .count(),
            pro_data_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.PRO_DATA) \
                .count(),
            mix_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.MIX) \
                .count(),
            other_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.OTHER) \
                .count(),
            unknown_tpns=TopPickNominationsArchive.objects \
                .filter(image__published__gt=cutoff) \
                .filter(image__data_source=DataSource.UNKNOWN) \
                .count(),
        )

    @staticmethod
    def user_has_submissions(user, days):
        return Image.objects.filter(
            Q(user=user) &
            Q(submitted_for_iotd_tp_consideration__isnull=False) &
            Q(submitted_for_iotd_tp_consideration__date__gt=DateTimeService.today() - timedelta(days=days))
        ).exists()

    @staticmethod
    def notify_about_upcoming_deadline_for_iotd_tp_submission():
        images = Image.objects.filter(
            published__date=DateTimeService.today() - timedelta(
                days=settings.IOTD_SUBMISSION_FOR_CONSIDERATION_WINDOW_DAYS -
                     settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS
            ),
            submitted_for_iotd_tp_consideration__isnull=True,
        )

        for image in images:
            if IotdService.user_has_submissions(image.user, 365):
                thumb = image.thumbnail_raw('gallery', None, sync=True)

                push_notification(
                    [image.user], None, 'iotd_tp_submission_deadline', {
                        'image': image,
                        'image_thumbnail': thumb.url if thumb else None,
                        'url': build_notification_url(settings.BASE_URL + image.get_absolute_url(), image.user),
                        'days': settings.IOTD_SUBMISSION_FOR_CONSIDERATION_REMINDER_DAYS,
                        'BASE_URL': settings.BASE_URL,
                    }
                )

    @staticmethod
    def get_recently_expired_unsubmitted_images(d: timedelta) -> QuerySet:
        """
            Gets images that:
              - didn't get dismissed
              - didn't get enough submissions to advance to the reviewers' queue
              - are about to the exit the submitters' queues
        :param d: how long ago the image still has until expiration
        :return: the queryset of images
        """

        deadline_lower: datetime = DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS)
        deadline_upper: datetime = DateTimeService.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS) + d
        submitted_time_query: Q = \
            Q(submitted_for_iotd_tp_consideration__gte=deadline_lower) & \
            Q(submitted_for_iotd_tp_consideration__lt=deadline_upper)
        dismissals_query: Q = Q(num_dismissals__lt=settings.IOTD_MAX_DISMISSALS)
        submissions_query: Q = Q(num_submissions__lt=settings.IOTD_SUBMISSION_MIN_PROMOTIONS)

        images: QuerySet = Image.objects \
            .annotate(
            num_dismissals=Count('iotddismissedimage', distinct=True),
            num_submissions=Count('iotdsubmission', distinct=True),
        ) \
            .filter(submitted_time_query & dismissals_query & submissions_query)

        return images

    @staticmethod
    def calculate_iotd_staff_members_stats(period_start: datetime, period_end: datetime):
        # Promoted an image that made it to IOTD
        guessed_iotd_reward = Decimal('4')
        # Promoted an image that made it to TP
        guessed_tp_reward = Decimal('2')
        # Promoted an image that made it to TPN
        guessed_tpn_reward = Decimal('1')
        # Dismissed an image that made it to IOTD
        canned_iotd_penalty = Decimal('40')
        # Dismissed an image that made it to TP
        canned_tp_penalty = Decimal('20')
        # Dismissed an image that made it to TPN
        canned_tpn_penalty = Decimal('10')
        # Dismissed an image that was dismissed by (settings.IOTD_MAX_DISMISSALS - 1) other users
        correct_dismissal_reward = Decimal('1')
        # Neglected to dismiss an image that was dismissed by settings.IOTD_MAX_DISMISSALS users
        missed_dismissal_penalty = Decimal('2')
        # Promoted an image that didn't get any awards
        wasted_promotion_penalty = Decimal('0.5')
        # Neglected to promote an image that made it to IOTD
        missed_iotd_submission_penalty = Decimal('2')
        # Neglected to promote an image that made it to TP
        missed_tp_submission_penalty = Decimal('1')
        # Neglected to promote an image that made it to TPN
        missed_tpn_submission_penalty = Decimal('.5')

        submitters_scores = {}
        reviewers_scores = {}
        dismissal_scores = {}
        is_iotd_cache = {}
        is_top_pick_cache = {}
        is_top_pick_nomination_cache = {}

        def is_iotd(image):
            if image.id in is_iotd_cache:
                return is_iotd_cache[image.id]
            result = hasattr(image, 'iotd')
            is_iotd_cache[image.id] = result
            return result

        def is_top_pick(image):
            if image.id in is_top_pick_cache:
                return is_top_pick_cache[image.id]
            result = hasattr(image, 'toppickarchive')
            is_top_pick_cache[image.id] = result
            return result

        def is_top_pick_nomination(image):
            if image.id in is_top_pick_nomination_cache:
                return is_top_pick_nomination_cache[image.id]
            result = hasattr(image, 'toppicknominationsarchive')
            is_top_pick_nomination_cache[image.id] = result
            return result

        def get_submissions():
            return IotdSubmission.objects.filter(
                date__gte=period_start, date__lte=period_end
            ).select_related('image', 'submitter')

        def get_submissions_by_user(submissions):
            return {
                submission.submitter.username: set(
                    IotdSubmission.objects.filter(
                        submitter=submission.submitter, date__gte=period_start, date__lte=period_end
                    ).select_related('image').values_list('image_id', flat=True)
                )
                for submission in submissions
            }

        def get_dismissals_by_user(dismissals):
            dismissed_images = dismissals.values_list('user__username', 'image_id').order_by('user__username')
            dismissed_images_dict = defaultdict(list)
            for username, image_id in dismissed_images:
                dismissed_images_dict[username].append(image_id)
            return dict(dismissed_images_dict)

        def get_votes():
            return IotdVote.objects.filter(
                date__gte=period_start, date__lte=period_end
            ).select_related('image', 'reviewer')

        def get_dismissals():
            return IotdDismissedImage.objects.filter(
                created__gte=period_start, created__lte=period_end
            ).select_related('image', 'user')

        def prepare_dismissals_counts(dismissals):
            counts = {}
            for dismissal in dismissals:
                image_id = dismissal.image_id
                counts[image_id] = counts.get(image_id, 0) + 1
            return counts

        def get_seen_images_by_user():
            prefetch = Prefetch(
                'iotdsubmitterseenimage_set',
                queryset=IotdSubmitterSeenImage.objects.filter(created__gte=period_start, created__lte=period_end),
                to_attr='seen_images'
            )

            # Get all users who have seen images, prefetching the filtered seen images
            users = User.objects.prefetch_related(prefetch).all()

            # Build the dictionary with a single database query
            return {
                user.username: {seen_image.image_id for seen_image in user.seen_images}
                for user in users
            }

        def prepare_submitter_scores(submissions, dismissals):
            for submission in submissions:
                if not submission.submitter:
                    continue

                submitter_username = submission.submitter.username
                score = submitters_scores.get(submitter_username, 0)

                if is_iotd(submission.image):
                    score += guessed_iotd_reward
                    submitter_promotion_counts[submitter_username]['iotds'] += 1
                elif is_top_pick(submission.image):
                    score += guessed_tp_reward
                    submitter_promotion_counts[submitter_username]['top_picks'] += 1
                elif is_top_pick_nomination(submission.image):
                    score += guessed_tpn_reward
                    submitter_promotion_counts[submitter_username]['top_pick_nominations'] += 1
                else:
                    score -= wasted_promotion_penalty
                    submitter_promotion_counts[submitter_username]['wasted_promotions'] += 1

                submitters_scores[submitter_username] = score

                # Increment promotion counts
                submitter_promotion_counts[submitter_username]['promotions'] += 1

            # Update scoring for missed submissions and dismissals
            for submitter_username, seen_image_ids in seen_images_by_user.items():
                submitted_image_ids = submissions_by_user.get(submitter_username, set())
                dismissed_image_ids = dismissals_by_user.get(submitter_username, set())

                for image_id in seen_image_ids:
                    try:
                        image = Image.objects_including_wip.get(pk=image_id)
                    except Image.DoesNotExist:
                        # In case the image was deleted.
                        continue
                    if image_id not in submitted_image_ids:
                        # Submitter saw an image that was promoted but did not submit it
                        score = 0
                        if is_iotd(image):
                            score = submitters_scores.get(submitter_username, 0) - missed_iotd_submission_penalty
                            submitter_promotion_counts[submitter_username]['missed_iotd_promotions'] += 1
                        elif is_top_pick(image):
                            score = submitters_scores.get(submitter_username, 0) - missed_tp_submission_penalty
                            submitter_promotion_counts[submitter_username]['missed_tp_promotions'] += 1
                        elif is_top_pick_nomination(image):
                            score = submitters_scores.get(submitter_username, 0) - missed_tpn_submission_penalty
                            submitter_promotion_counts[submitter_username]['missed_tpn_promotions'] += 1
                        submitters_scores[submitter_username] = score

                    if image_id not in dismissed_image_ids:
                        # Submitter saw an image that was dismissed by others but did not submit it
                        try:
                            dismissed = image_dismissal_counts[image_id] >= settings.IOTD_MAX_DISMISSALS
                            if dismissed:
                                score = submitters_scores.get(submitter_username, 0) - missed_dismissal_penalty
                                submitters_scores[submitter_username] = score
                                dismissal_counts[submitter_username]['missed_dismissals'] += 1
                        except KeyError:
                            # Nobody dismissed this
                            continue

        def prepare_reviewer_scores(votes):
            for vote in votes:
                if not vote.reviewer:
                    continue

                reviewer_username = vote.reviewer.username
                score = reviewers_scores.get(reviewer_username, 0)

                if is_iotd(vote.image):
                    score += guessed_iotd_reward
                elif is_top_pick(vote.image):
                    score += guessed_tp_reward

                reviewers_scores[reviewer_username] = score

                # Increment promotion counts
                reviewer_promotion_counts[reviewer_username]['promotions'] += 1
                if is_iotd(vote.image):
                    reviewer_promotion_counts[reviewer_username]['iotds'] += 1
                elif is_top_pick(vote.image):
                    reviewer_promotion_counts[reviewer_username]['top_picks'] += 1
                else:
                    score -= wasted_promotion_penalty
                    reviewer_promotion_counts[reviewer_username]['wasted_promotions'] += 1

        def remove_inactive_reviewers(reviewers_scores, reviewer_promotion_counts):
            return {
                username: score
                for username, score in reviewers_scores.items()
                if reviewer_promotion_counts[username]['promotions'] > 0
            }

        def prepare_dismissal_scores(dismissals):
            for dismissal in dismissals:
                if not dismissal.user:
                    continue

                user_username = dismissal.user.username
                image_id = dismissal.image_id

                # Fetch current scores
                dismissal_score = dismissal_scores.get(user_username, 0)

                # Check if the dismissal was correct (at least settings.IOTD_MAX_DISMISSALS other dismissals)
                correct_dismissal = image_dismissal_counts[image_id] >= settings.IOTD_MAX_DISMISSALS

                if correct_dismissal:
                    dismissal_scores[user_username] = dismissal_score + correct_dismissal_reward
                    # Update correct dismissal counts
                    dismissal_counts[user_username]['correct_dismissals'] += 1
                else:
                    if is_iotd(dismissal.image):
                        dismissal_scores[user_username] = dismissal_score - canned_iotd_penalty
                        dismissal_counts[user_username]['iotds'] += 1
                    elif is_top_pick(dismissal.image):
                        dismissal_scores[user_username] = dismissal_score - canned_tp_penalty
                        dismissal_counts[user_username]['top_picks'] += 1
                    elif is_top_pick_nomination(dismissal.image):
                        dismissal_scores[user_username] = dismissal_score - canned_tpn_penalty
                        dismissal_counts[user_username]['top_pick_nominations'] += 1

                dismissal_counts[user_username]['dismissals'] += 1

        def prepare_active_days(submissions, votes, dismissals):
            for username in all_usernames:
                days_with_submissions = list(
                    submissions.filter(submitter__username=username).values_list('date__date', flat=True).distinct()
                )
                days_with_votes = list(
                    votes.filter(reviewer__username=username).values_list('date__date', flat=True).distinct()
                )
                days_with_dismissals = list(
                    dismissals.filter(user__username=username).values_list('created__date', flat=True).distinct()
                )
                submitter_promotion_counts[username]['active_days'] = len(
                    set(days_with_submissions + days_with_votes + days_with_dismissals)
                )

        def combined_score(submitter_score, reviewer_score, dismissal_score):
            return submitter_score + reviewer_score + dismissal_score

        def combine_counts(submitter_counts, reviewer_counts):
            combined = {}

            for key in set(submitter_counts) | set(reviewer_counts):
                combined[key] = submitter_counts.get(key, 0) + reviewer_counts.get(key, 0)
            return combined

        def prepare_combined_data():
            combined_data = {}

            for user in set(submitters_scores) | set(reviewers_scores) | set(dismissal_scores):
                combined_data[user] = {
                    'score': combined_score(
                        submitters_scores.get(user, Decimal('0')),
                        reviewers_scores.get(user, Decimal('0')),
                        dismissal_scores.get(user, Decimal('0'))
                    ),
                    'promotions': combine_counts(
                        submitter_promotion_counts.get(user, {}),
                        reviewer_promotion_counts.get(user, {})
                    ),
                    'dismissals': dismissal_counts.get(user, {}),
                }

            return combined_data

        submissions = get_submissions()
        dismissals = get_dismissals()
        submissions_by_user = get_submissions_by_user(submissions)
        dismissals_by_user = get_dismissals_by_user(dismissals)
        votes = get_votes()
        image_dismissal_counts = prepare_dismissals_counts(dismissals)
        seen_images_by_user = get_seen_images_by_user()

        all_usernames = set()
        all_usernames.update(submission.submitter.username for submission in submissions if submission.submitter)
        all_usernames.update(vote.reviewer.username for vote in votes if vote.reviewer)
        all_usernames.update(dismissal.user.username for dismissal in dismissals if dismissal.user)

        submitter_promotion_counts = {
            username: {
                'promotions': 0,
                'wasted_promotions': 0,
                'missed_iotd_promotions': 0,
                'missed_tp_promotions': 0,
                'missed_tpn_promotions': 0,
                'top_pick_nominations': 0,
                'top_picks': 0,
                'iotds': 0,
                'active_days': 0
            } for username in all_usernames
        }

        reviewer_promotion_counts = {
            username: {
                'promotions': 0,
                'wasted_promotions': 0,
                'missed_iotd_promotions': 0,
                'missed_tp_promotions': 0,
                'missed_tpn_promotions': 0,
                'top_pick_nominations': 0,
                'top_picks': 0,
                'iotds': 0,
                'active_days': 0
            } for username in all_usernames
        }

        dismissal_counts = {
            username: {
                'dismissals': 0,
                'correct_dismissals': 0,
                'missed_dismissals': 0,
                'top_pick_nominations': 0,
                'top_picks': 0,
                'iotds': 0
            } for username in all_usernames
        }

        prepare_submitter_scores(submissions, dismissals)
        prepare_reviewer_scores(votes)
        prepare_dismissal_scores(dismissals)
        prepare_active_days(submissions, votes, dismissals)
        reviewers_scores = remove_inactive_reviewers(reviewers_scores, reviewer_promotion_counts)

        combined_data = prepare_combined_data()

        # Print the merged data
        log.debug(
            "User,Score,Active days,Promotions/Dismissals accuracy ratio,"
            "Promotions,Wasted Promotions,Missed IOTD Promotions,Missed TP Promotion,Missed TPN Promotions,"
            "TPNs,TPs,IOTDs,"
            "Dismissals,Correct Dismissals,Missed Dismissals,"
            "TPNs,TPs,IOTDs"
        )
        for username, data in sorted(combined_data.items(), key=lambda item: item[1]['score'], reverse=True):
            try:
                promotions_dismissals_accuracy_ratio = (
                                                               data['promotions'].get('top_pick_nominations', 0) +
                                                               data['promotions'].get('top_picks', 0) +
                                                               data['promotions'].get('iotds', 0)
                                                       ) / (
                                                               data['dismissals'].get('top_pick_nominations', 0) +
                                                               data['dismissals'].get('top_picks', 0) +
                                                               data['dismissals'].get('iotds', 0)
                                                       )
            except ZeroDivisionError:
                promotions_dismissals_accuracy_ratio = 0

            log.debug(
                f"{username},"
                f"{data['score']},"
                f"{data['promotions'].get('active_days', 0)},"
                f"{promotions_dismissals_accuracy_ratio:.2f},"
                f"{data['promotions'].get('promotions', 0)},"
                f"{data['promotions'].get('wasted_promotions', 0)},"
                f"{data['promotions'].get('missed_iotd_promotions', 0)},"
                f"{data['promotions'].get('missed_tp_promotions', 0)},"
                f"{data['promotions'].get('missed_tpn_promotions', 0)},"
                f"{data['promotions'].get('top_pick_nominations', 0)},"
                f"{data['promotions'].get('top_picks', 0)},"
                f"{data['promotions'].get('iotds', 0)},"
                f"{data['dismissals'].get('dismissals', 0)},"
                f"{data['dismissals'].get('correct_dismissals', 0)},"
                f"{data['dismissals'].get('missed_dismissals', 0)},"
                f"{data['dismissals'].get('top_pick_nominations', 0)},"
                f"{data['dismissals'].get('top_picks', 0)},"
                f"{data['dismissals'].get('iotds', 0)}"
            )
            IotdStaffMemberScore.objects.create(
                user=User.objects.get(username=username),
                period_start=period_start,
                period_end=period_end,
                score=data['score'],
                active_days=data['promotions'].get('active_days', 0),
                promotions_dismissals_accuracy_ratio=promotions_dismissals_accuracy_ratio,
                promotions=data['promotions'].get('promotions', 0),
                wasted_promotions=data['promotions'].get('wasted_promotions', 0),
                missed_iotd_promotions=data['promotions'].get('missed_iotd_promotions', 0),
                missed_tp_promotions=data['promotions'].get('missed_tp_promotions', 0),
                missed_tpn_promotions=data['promotions'].get('missed_tpn_promotions', 0),
                promotions_to_tpn=data['promotions'].get('top_pick_nominations', 0),
                promotions_to_tp=data['promotions'].get('top_picks', 0),
                promotions_to_iotd=data['promotions'].get('iotds', 0),
                dismissals=data['dismissals'].get('dismissals', 0),
                correct_dismissals=data['dismissals'].get('correct_dismissals', 0),
                missed_dismissals=data['dismissals'].get('missed_dismissals', 0),
                dismissals_to_tpn=data['dismissals'].get('top_pick_nominations', 0),
                dismissals_to_tp=data['dismissals'].get('top_picks', 0),
                dismissals_to_iotd=data['dismissals'].get('iotds', 0),
            )

    @staticmethod
    def may_auto_submit_to_iotd_tp_process(user: User) -> bool:
        q = Q(image__user=user) | Q(image__collaborators=user)
        has_top_picks = TopPickArchive.objects.filter(q).exists()
        has_iotd = Iotd.objects.filter(q).exists()

        return has_top_picks or has_iotd
