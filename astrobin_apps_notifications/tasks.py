import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django_bouncy.models import Delivery, Bounce, Complaint

from astrobin.models import Image, UserProfile, ImageRevision
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from common.services import DateTimeService
from toggleproperties.models import ToggleProperty


logger = logging.getLogger('apps')

@shared_task(time_limit=300)
def purge_old_notifications():
    call_command("purge_old_notifications")


@shared_task(time_limit=1800)
def push_notification_for_new_image(user_pk, image_pk):
    try:
        image = Image.objects_including_wip.get(pk=image_pk)
    except Image.DoesNotExist:
        logger.error('push_notification_for_new_image called for image not found: %d' % image_pk)
        return

    if image.is_wip:
        logger.error('push_notification_for_new_image called for image that is wip: %d' % image_pk)
        return

    followers = [
        x.user for x in
        ToggleProperty.objects.toggleproperties_for_object(
            "follow",
            UserProfile.objects.get(user__pk=user_pk).user)
    ]

    if len(followers) > 0:
        thumb = image.thumbnail_raw('gallery', None, sync=True)
        push_notification(followers, image.user, 'new_image', {
            'image': image,
            'image_thumbnail': thumb.url if thumb else None
        })
    else:
        logger.error('push_notification_for_new_image called for image %d whose author %d has no followers' % (
            image_pk, user_pk)
        )


@shared_task(time_limit=1800)
def push_notification_for_new_image_revision(revision_pk):
    try:
        revision = ImageRevision.objects.get(pk=revision_pk)
    except ImageRevision.DoesNotExist:
        logger.error('push_notification_for_new_image called for revision not found: %d' % revision_pk)
        return

    if revision.skip_notifications or revision.image.is_wip:
        logger.error('push_notification_for_new_image called for revision of image that is wip: %d' % revision_pk)
        return

    followers = [x.user for x in ToggleProperty.objects.filter(
        property_type="follow",
        content_type=ContentType.objects.get_for_model(User),
        object_id=revision.image.user.pk)]

    if len(followers) > 0:
        push_notification(followers, revision.image.user, 'new_image_revision', {
            'object_url': build_notification_url(settings.BASE_URL + revision.get_absolute_url(), revision.image.user),
            'originator': revision.image.user.userprofile.get_display_name(),
        })
    else:
        logger.error(
            'push_notification_for_new_image called for revision %d whose author has no followers' % revision_pk
        )


@shared_task(time_limit=300, acks_late=True)
def clear_old_bouncy_objects():
    Delivery.objects.filter(created_at__lte=DateTimeService.now() - timedelta(7)).delete()
    Bounce.objects.filter(created_at__lte=DateTimeService.now() - timedelta(30)).delete()
    Complaint.objects.filter(created_at__lte=DateTimeService.now() - timedelta(90)).delete()
