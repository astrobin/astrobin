import logging
from datetime import date, datetime, timedelta
from typing import List, Union

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.db import IntegrityError
from django.db.models import Count, OuterRef, Q, QuerySet, Subquery
from django.utils import timezone
from django.utils.translation import gettext

from astrobin.enums import SubjectType
from astrobin.enums.data_source import DataSource
from astrobin.enums.moderator_decision import ModeratorDecision
from astrobin.models import Image
from astrobin_apps_images.services import ImageService
from astrobin_apps_iotd.models import (
    Iotd, IotdJudgementQueueEntry, IotdQueueSortOrder, IotdReviewQueueEntry, IotdStaffMemberSettings, IotdStats,
    IotdSubmission,
    IotdSubmissionQueueEntry, IotdVote,
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
    def is_in_iotd_queue(self, image: Image) -> bool:
        return (
                IotdSubmissionQueueEntry.objects.filter(image=image).exists() or
                IotdReviewQueueEntry.objects.filter(image=image).exists() or
                IotdJudgementQueueEntry.objects.filter(image=image).exists()
        )

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
            Q(image__deleted__isnull=True)
        )

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

        for entry in IotdSubmissionQueueEntry.objects \
                .select_related('image') \
                .prefetch_related('image__imaging_telescopes_2', 'image__imaging_cameras_2') \
                .filter(submitter=submitter) \
                .order_by(*order_by) \
                .iterator():
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

        for entry in IotdReviewQueueEntry.objects \
                .select_related('image') \
                .prefetch_related('image__imaging_telescopes_2', 'image__imaging_cameras_2') \
                .filter(reviewer=reviewer) \
                .order_by(*order_by) \
                .iterator():
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

        for entry in IotdJudgementQueueEntry.objects \
                .select_related('image') \
                .prefetch_related('image__imaging_telescopes_2', 'image__imaging_cameras_2') \
                .filter(judge=judge) \
                .order_by(*order_by) \
                .iterator():
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
        latest = TopPickNominationsArchive.objects.first()

        items = Image.objects.annotate(
            num_submissions=Count('iotdsubmission', distinct=True)
        ).filter(
            Q(
                Q(num_submissions__gte=settings.IOTD_SUBMISSION_MIN_PROMOTIONS) |
                Q(
                    Q(num_submissions__gt=0) &
                    Q(submitted_for_iotd_tp_consideration__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            ) &
            Q(submitted_for_iotd_tp_consideration__lt=datetime.now() - timedelta(settings.IOTD_SUBMISSION_WINDOW_DAYS))
        ).order_by('-submitted_for_iotd_tp_consideration')

        if latest:
            items = items.filter(
                submitted_for_iotd_tp_consideration__gt=latest.image.submitted_for_iotd_tp_consideration
            )

        items.update(updated=DateTimeService.now())

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
            Q(submitted_for_iotd_tp_consideration__lt=datetime.now() - timedelta(settings.IOTD_REVIEW_WINDOW_DAYS)) &
            Q(Q(iotd=None) | Q(iotd__date__gt=datetime.now().date())) &
            Q(
                Q(num_votes__gte=settings.IOTD_REVIEW_MIN_PROMOTIONS) |
                Q(
                    Q(num_votes__gt=0) &
                    Q(submitted_for_iotd_tp_consideration__lt=settings.IOTD_MULTIPLE_PROMOTIONS_REQUIREMENT_START)
                )
            )
        ).order_by('-submitted_for_iotd_tp_consideration')

        if latest:
            items = items.filter(
                submitted_for_iotd_tp_consideration__gt=latest.image.submitted_for_iotd_tp_consideration
            )

        items.update(updated=DateTimeService.now())

        for item in items.iterator():
            try:
                TopPickArchive.objects.create(image=item)
            except IntegrityError:
                continue

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
                log.debug(
                    f'Image {image.get_id()} "{image.title}" assigned to judge {judge.pk} "{judge.username}".'
                )

    def clear_stale_queue_entries(self):
        IotdSubmissionQueueEntry.objects.exclude(submitter__groups__name=GroupName.IOTD_SUBMITTERS).delete()
        IotdReviewQueueEntry.objects.exclude(reviewer__groups__name=GroupName.IOTD_REVIEWERS).delete()
        IotdJudgementQueueEntry.objects.exclude(judge__groups__name=GroupName.IOTD_JUDGES).delete()

    def get_inactive_submitter_and_reviewers(self, days):
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
    def submit_to_iotd_tp_process(user: User, image: Image, auto_submit=False):
        may, reason = IotdService.may_submit_to_iotd_tp_process(user, image)

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

            if auto_submit:
                image.user.userprofile.auto_submit_to_iotd_tp_process = True
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
    def may_submit_to_iotd_tp_process(user: User, image: Image):
        if not user.is_authenticated:
            return False, MayNotSubmitToIotdTpReason.NOT_AUTHENTICATED

        if user != image.user:
            return False, MayNotSubmitToIotdTpReason.NOT_OWNER

        if image.submitted_for_iotd_tp_consideration is not None:
            return False, MayNotSubmitToIotdTpReason.ALREADY_SUBMITTED

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
        ):
            return False, MayNotSubmitToIotdTpReason.NO_ACQUISITIONS

        if image.user.userprofile.exclude_from_competitions:
            return False, MayNotSubmitToIotdTpReason.EXCLUDED_FROM_COMPETITIONS

        if image.user.userprofile.banned_from_competitions:
            return False, MayNotSubmitToIotdTpReason.BANNED_FROM_COMPETITIONS

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
