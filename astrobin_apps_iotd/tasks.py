import logging
import math

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import Group

from astrobin_apps_iotd.models import Iotd, IotdSubmission, IotdVote
from astrobin_apps_iotd.services import IotdService
from astrobin_apps_notifications.utils import push_notification
from common.services import DateTimeService

logger = logging.getLogger('apps')


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
            member.groups.remove(Group.objects.get(name='iotd_staff'))
            member.groups.remove(Group.objects.get(name='iotd_reviewers'))
            member.groups.remove(Group.objects.get(name='iotd_submitters'))

        push_notification(final_notice_members, 'iotd_staff_inactive_removal_notice', {
            'BASE_URL': settings.BASE_URL,
            'days': final_notice_days,
            'max_inactivity_days': final_notice_days
        })
        return

    reminder_2_days = int(math.ceil(final_notice_days / 2))
    reminder_2_members = IotdService().get_inactive_submitter_and_reviewers(reminder_2_days)
    if reminder_2_members:
        push_notification(reminder_2_members, 'iotd_staff_inactive_warning', {
            'BASE_URL': settings.BASE_URL,
            'days': reminder_2_days,
            'max_inactivity_days': final_notice_days
        })
        return

    reminder_1_days = int(math.ceil(final_notice_days / 4))
    reminder_1_members = IotdService().get_inactive_submitter_and_reviewers(reminder_1_days)
    if reminder_1_members:
        push_notification(reminder_1_members, 'iotd_staff_inactive_warning', {
            'BASE_URL': settings.BASE_URL,
            'days': reminder_1_days,
            'max_inactivity_days': final_notice_days
        })


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
    push_notification(submitters, 'image_you_promoted_is_iotd', {
        'image': image,
        'image_thumbnail': thumb.url if thumb else None
    })

    reviewers = [x.reviewer for x in IotdVote.objects.filter(image=image)]
    push_notification(reviewers, 'image_you_promoted_is_iotd', {
        'image': image,
        'image_thumbnail': thumb.url if thumb else None
    })
