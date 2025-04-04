import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.core.mail import mail_admins
from django.db.models import Q, QuerySet

from astrobin.models import Image
from astrobin_apps_iotd.models import (
    Iotd, IotdDismissedImage, IotdStaffMemberScore, IotdSubmission,
    IotdSubmitterSeenImage, IotdVote,
)
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_notifications.services.notifications_service import NotificationContext
from astrobin_apps_notifications.utils import push_notification
from common.constants import GroupName
from common.services import DateTimeService
from common.utils import get_segregated_reader_database

logger = logging.getLogger(__name__)


@shared_task(time_limit=900)
def update_top_pick_nomination_archive():
    IotdService().update_top_pick_nomination_archive()


@shared_task(time_limit=900)
def update_top_pick_archive():
    IotdService().update_top_pick_archive()


@shared_task(time_limit=900)
def send_iotd_staff_insufficiently_active_reminders_and_remove_after_max_reminders():
    min_promotions_per_period = getattr(settings, 'IOTD_MIN_PROMOTIONS_PER_PERIOD', '7/7')
    min_promotions = int(min_promotions_per_period.split('/')[0])
    days = int(min_promotions_per_period.split('/')[1])
    max_reminders = 2

    insufficiently_active_members = IotdService().get_insufficiently_active_submitters_and_reviewers()

    for member in insufficiently_active_members:
        if (member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent or 0) >= max_reminders:
            # Determine member roles before removing them
            was_reviewer = member.groups.filter(name=GroupName.IOTD_REVIEWERS).exists()
            was_submitter = member.groups.filter(name=GroupName.IOTD_SUBMITTERS).exists()
            
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_STAFF))
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_REVIEWERS))
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_SUBMITTERS))
            member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 0
            member.userprofile.save(keep_deleted=True)
            
            roles = []
            if was_submitter:
                roles.append("Submitter")
            if was_reviewer:
                roles.append("Reviewer")
                
            role_str = " and ".join(roles)
            logger.info(
                f"Removed {member.username}/{member.pk} ({role_str}) from IOTD staff groups due to insufficient "
                f"activity"
            )
            
            # Email admins about the removal
            mail_admins(
                subject=f"IOTD: {member.username} ({role_str}) removed from staff due to inactivity",
                message=f"User {member.username} (ID: {member.pk}) has been removed from the IOTD staff groups.\n\n"
                        f"Role(s): {role_str}\n\n"
                        f"Reason: They did not meet the minimum requirement of {min_promotions} promotions in {days}"
                        f" days after receiving {max_reminders} reminders."
            )

            push_notification(
                [member], None, 'iotd_staff_inactive_removal_notice', {
                    'BASE_URL': settings.BASE_URL,
                    'days': 0,
                    'max_inactivity_days': 0,
                    'min_promotions': min_promotions,
                    'min_promotions_days': days,
                    'max_reminders': max_reminders,
                    'extra_tags': {
                        'context': NotificationContext.IOTD
                    },
                }
            )
        else:
            if member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent is None:
                member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent = 1
            else:
                member.userprofile.insufficiently_active_iotd_staff_member_reminders_sent += 1
            member.userprofile.save(keep_deleted=True)

            push_notification(
                [member], None, 'iotd_staff_insufficiently_active_warning', {
                    'BASE_URL': settings.BASE_URL,
                    'min_promotions': min_promotions,
                    'min_promotions_days': days,
                    'extra_tags': {
                        'context': NotificationContext.IOTD
                    },
                }
            )


@shared_task(time_limit=180)
def send_iotd_staff_inactive_reminders_and_remove_after_max_days():
    final_notice_days = settings.IOTD_MAX_INACTIVE_DAYS
    final_notice_members = IotdService().get_inactive_submitters_and_reviewers(final_notice_days)
    if final_notice_members:
        for member in final_notice_members:
            # Determine member roles before removing them
            was_reviewer = member.groups.filter(name=GroupName.IOTD_REVIEWERS).exists()
            was_submitter = member.groups.filter(name=GroupName.IOTD_SUBMITTERS).exists()
            
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_STAFF))

            if was_reviewer:
                member.groups.remove(Group.objects.get(name=GroupName.IOTD_REVIEWERS))
                logger.info(f"Removed {member.username}/{member.pk} from IOTD_REVIEWERS group")

            if was_submitter:
                member.groups.remove(Group.objects.get(name=GroupName.IOTD_SUBMITTERS))
                logger.info(f"Removed {member.username}/{member.pk} from IOTD_SUBMITTERS group")
                
            roles = []
            if was_submitter:
                roles.append("Submitter")
            if was_reviewer:
                roles.append("Reviewer")
                
            role_str = " and ".join(roles)
            
            # Email admins about the removal
            mail_admins(
                subject=f"IOTD: {member.username} ({role_str}) removed from staff due to inactivity",
                message=f"User {member.username} (ID: {member.pk}) has been removed from the IOTD staff groups.\n\n"
                        f"Role(s): {role_str}\n\n"
                        f"Reason: They have been inactive for {final_notice_days} days."
            )

        push_notification(final_notice_members, None, 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': final_notice_days,
            'max_inactivity_days': final_notice_days,
            'extra_tags': {
                'context': NotificationContext.IOTD
            },
        })
        return

    reminder_2_days = settings.IOTD_INACTIVE_MEMBER_REMINDER_2_DAYS
    reminder_2_members = IotdService().get_inactive_submitters_and_reviewers(reminder_2_days)
    if reminder_2_members:
        push_notification(reminder_2_members, None, 'iotd_staff_inactive_warning', {
            'BASE_URL': settings.BASE_URL,
            'days': reminder_2_days,
            'max_inactivity_days': final_notice_days,
            'extra_tags': {
                'context': NotificationContext.IOTD
            },
        })
        return

    reminder_1_days = settings.IOTD_INACTIVE_MEMBER_REMINDER_1_DAYS
    reminder_1_members = IotdService().get_inactive_submitters_and_reviewers(reminder_1_days)
    if reminder_1_members:
        push_notification(
            reminder_1_members, None, 'iotd_staff_inactive_warning', {
                'BASE_URL': settings.BASE_URL,
                'days': reminder_1_days,
                'max_inactivity_days': final_notice_days,
                'extra_tags': {
                    'context': NotificationContext.IOTD
                },
            }
        )


@shared_task(time_limit=60)
def clear_stale_queue_entries():
    IotdService().clear_stale_queue_entries()


@shared_task(time_limit=180)
def send_notifications_when_promoted_image_becomes_iotd():
    try:
        iotd = Iotd.objects.get(date=DateTimeService.today())
    except Iotd.DoesNotExist:
        logger.error("send_notifications_when_promoted_image_becomes_iotd: Iotd not found")
        return

    image = iotd.image
    thumb = image.thumbnail_raw('gallery', None, sync=True)

    submitters = [
        x.submitter for x in IotdSubmission.objects.filter(image=image)
    ]
    push_notification(submitters, None, 'image_you_promoted_is_iotd', {
        'preheader': image.title,
        'image': image,
        'image_thumbnail': thumb.url if thumb else None,
        'extra_tags': {
            'context': NotificationContext.IMAGE,
            'image_id': image.get_id(),
        },
    })

    reviewers = [x.reviewer for x in IotdVote.objects.filter(image=image)]
    push_notification(reviewers, None, 'image_you_promoted_is_iotd', {
        'preheader': image.title,
        'image': image,
        'image_thumbnail': thumb.url if thumb else None,
        'extra_tags': {
            'context': NotificationContext.IMAGE,
            'image_id': image.get_id(),
        },
    })

    dismissers = [
        x.user for x in IotdDismissedImage.objects.filter(image=image)
    ]
    push_notification(
        dismissers, None, 'image_you_dismissed_is_iotd', {
            'preheader': image.title,
            'image': image,
            'image_thumbnail': thumb.url if thumb else None,
            'extra_tags': {
                'context': NotificationContext.IMAGE,
                'image_id': image.get_id(),
            },
        }
    )

    collaborators = [image.user] + list(image.collaborators.all())
    push_notification(collaborators, None, 'your_image_is_iotd', {
        'preheader': image.title,
        'image': image,
        'image_thumbnail': thumb.url if thumb else None,
        'extra_tags': {
            'context': NotificationContext.IMAGE,
            'image_id': image.get_id(),
        },
    })


@shared_task(time_limit=840, acks_late=True)
def update_submission_queues():
    logger.info("update_submission_queues started")
    IotdService().update_submission_queues()
    logger.info("update_submission_queues completed")


@shared_task(time_limit=840, acks_late=True)
def update_review_queues():
    logger.info("update_review_queues started")
    IotdService().update_review_queues()
    logger.info("update_review_queues completed")


@shared_task(time_limit=840, acks_late=True)
def update_judgement_queues():
    logger.info("update_judgement_queues started")
    IotdService().update_judgement_queues()
    logger.info("update_judgement_queues completed")


@shared_task(time_limit=600)
def update_stats():
    logger.info("update_stats started")
    IotdService().update_stats(365)
    logger.info("update_stats completed")


@shared_task(time_limit=600)
def notify_about_upcoming_deadline_for_iotd_tp_submission():
    IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()


@shared_task(time_limit=600, acks_late=True)
def resubmit_images_for_iotd_tp_consideration_if_they_did_not_get_enough_views():
    # Run this task every hour.
    last_check_cache_key = 'last_iotd_tp_resubmission_check'
    last_check: datetime = cache.get(last_check_cache_key)

    if last_check:
        delta: timedelta = datetime.now() - last_check
    else:
        logger.warning("last_iotd_tp_resubmission_check not found. Defaulting to 2 hours.")
        delta = timedelta(hours=2)

    recently_expired_images: QuerySet = IotdService.get_recently_expired_unsubmitted_images(delta).filter(
        submitted_for_iotd_tp_consideration__lt=DateTimeService.now() - delta
    )
    total_submitters: int = Group.objects.get(name=GroupName.IOTD_SUBMITTERS).user_set.count()
    min_percentage: float = settings.IOTD_DESIGNATED_SUBMITTERS_PERCENTAGE / 100 * .8

    image: Image
    for image in recently_expired_images.iterator():
        users_who_saw_this = IotdSubmitterSeenImage.objects \
            .using(get_segregated_reader_database()) \
            .filter(image=image) \
            .values_list('user', flat=True) \
            .distinct() \
            .count()
        if users_who_saw_this < float(total_submitters) * min_percentage:
            IotdService.resubmit_to_iotd_tp_process(image.user, image)

    cache.set(last_check_cache_key, datetime.now(), 60 * 60 * 24)


@shared_task(time_limit=3600, acks_late=True)
def calculate_iotd_staff_members_stats():
    service = IotdService()

    current_date = datetime.now()

    # Get the first day of the current month with time 00:00:00
    first_day_current_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Get the first day of two months ago with time 00:00:00
    # We first subtract 1 day to go to the previous month, then replace the day with 1
    first_day_previous_month = (first_day_current_month - timedelta(days=1)).replace(day=1)
    first_day_two_months_ago = (first_day_previous_month - timedelta(days=1)).replace(day=1)

    # Get the last day of two months ago with time 23:59:59.999
    # This is the day before the first day of the previous month
    last_day_two_months_ago = first_day_previous_month - timedelta(days=1)
    last_day_two_months_ago = last_day_two_months_ago.replace(hour=23, minute=59, second=59, microsecond=999999)

    service.calculate_iotd_staff_members_stats(first_day_two_months_ago, last_day_two_months_ago)

    staff_members = User.objects.filter(
        Q(groups__name=GroupName.IOTD_SUBMITTERS) | Q(groups__name=GroupName.IOTD_REVIEWERS)
    ).distinct()

    for user in staff_members.iterator():
        stats = IotdStaffMemberScore.objects.filter(
            user=user
        ).order_by(
            '-pk'
        ).first()

        if stats:
            push_notification(
                [user], None, 'your_iotd_staff_member_stats', {
                    'BASE_URL': settings.BASE_URL,
                    'stats': stats,
                    'extra_tags': {
                        'context': NotificationContext.IOTD
                    },
                }
            )
