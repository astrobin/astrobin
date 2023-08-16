import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import Group

from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_notifications.utils import push_notification
from common.constants import GroupName
from common.services import DateTimeService

logger = logging.getLogger(__name__)


@shared_task(time_limit=600)
def update_top_pick_nomination_archive():
    IotdService().update_top_pick_nomination_archive()


@shared_task(time_limit=600)
def update_top_pick_archive():
    IotdService().update_top_pick_archive()


@shared_task(time_limit=180)
def send_iotd_staff_inactive_reminders_and_remove_after_max_days():
    final_notice_days = settings.IOTD_MAX_INACTIVE_DAYS
    final_notice_members = IotdService().get_inactive_submitter_and_reviewers(final_notice_days)
    if final_notice_members:
        for member in final_notice_members:
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_STAFF))
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_REVIEWERS))
            member.groups.remove(Group.objects.get(name=GroupName.IOTD_SUBMITTERS))

        push_notification(final_notice_members, None, 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': final_notice_days,
            'max_inactivity_days': final_notice_days
        })
        return

    reminder_2_days = settings.IOTD_INACTIVE_MEMBER_REMINDER_2_DAYS
    reminder_2_members = IotdService().get_inactive_submitter_and_reviewers(reminder_2_days)
    if reminder_2_members:
        push_notification(reminder_2_members, None, 'iotd_staff_inactive_warning', {
            'BASE_URL': settings.BASE_URL,
            'days': reminder_2_days,
            'max_inactivity_days': final_notice_days
        })
        return

    reminder_1_days = settings.IOTD_INACTIVE_MEMBER_REMINDER_1_DAYS
    reminder_1_members = IotdService().get_inactive_submitter_and_reviewers(reminder_1_days)
    if reminder_1_members:
        push_notification(
            reminder_1_members, None, 'iotd_staff_inactive_warning', {
                'BASE_URL': settings.BASE_URL,
                'days': reminder_1_days,
                'max_inactivity_days': final_notice_days
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

    submitters = [x.submitter for x in IotdSubmission.objects.filter(image=image)]
    push_notification(submitters, None, 'image_you_promoted_is_iotd', {
        'image': image,
        'image_thumbnail': thumb.url if thumb else None
    })

    reviewers = [x.reviewer for x in IotdVote.objects.filter(image=image)]
    push_notification(reviewers, None, 'image_you_promoted_is_iotd', {
        'image': image,
        'image_thumbnail': thumb.url if thumb else None
    })

    push_notification([image.user], None, 'your_image_is_iotd', {
        'image': image,
        'image_thumbnail': thumb.url if thumb else None
    })


@shared_task(time_limit=840)
def update_submission_queues():
    IotdService().update_submission_queues()
    logger.info("update_submission_queues completed")


@shared_task(time_limit=840)
def update_review_queues():
    IotdService().update_review_queues()
    logger.info("update_review_queues completed")


@shared_task(time_limit=840)
def update_judgement_queues():
    IotdService().update_judgement_queues()
    logger.info("update_judgement_queues completed")


@shared_task(time_limit=600)
def update_stats():
    IotdService().update_stats(365)
    logger.info("update_stats completed")


@shared_task(time_limit=600)
def notify_about_upcoming_deadline_for_iotd_tp_submission():
    IotdService.notify_about_upcoming_deadline_for_iotd_tp_submission()
