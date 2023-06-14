import logging
from datetime import timedelta, datetime

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.utils import formats
from django_bouncy.models import Delivery, Bounce, Complaint

from astrobin.models import Image, UserProfile, ImageRevision
from astrobin_apps_notifications.utils import push_notification, build_notification_url
from common.services import AppRedirectionService, DateTimeService
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)


@shared_task(time_limit=300)
def purge_old_notifications():
    call_command("purge_old_notifications")


@shared_task(time_limit=1800)
def push_notification_for_new_image(image_pk):
    try:
        image = Image.objects_including_wip.get(pk=image_pk)
    except Image.DoesNotExist:
        logger.error('push_notification_for_new_image called for image not found: %d' % image_pk)
        return

    if image.is_wip:
        logger.error('push_notification_for_new_image called for image that is wip: %d' % image_pk)
        return

    user_pks = [image.user.pk] + list(image.collaborators.all().values_list('pk', flat=True))

    user_followers = list(set([x.user for x in ToggleProperty.objects.filter(
        property_type="follow",
        content_type=ContentType.objects.get_for_model(User),
        object_id__in=user_pks
    ).order_by('object_id')]))

    equipment_dictionary = {}

    for equipment_item_class in [
        'imaging_telescopes_2',
        'imaging_cameras_2',
        'mounts_2',
        'filters_2',
        'accessories_2',
        'software_2',
        'guiding_telescopes_2',
        'guiding_cameras_2',
    ]:
        for equipment_item in getattr(image, equipment_item_class).all().iterator():
            key = f'{equipment_item.klass}-{equipment_item.pk}'  # unique key

            # Initialize the nested dictionary if it doesn't exist
            if key not in equipment_dictionary:
                equipment_dictionary[key] = {"item": equipment_item, "followers": []}

            # Create the list of ToggleProperty objects
            equipment_item_followers = list(
                set(
                    x.user for x in ToggleProperty.objects.filter(
                        property_type="follow",
                        content_type=ContentType.objects.get_for_model(equipment_item),
                        object_id=equipment_item.pk
                    ).order_by('object_id')
                )
            )

            # Remove the users who are in user_followers from the followers list
            equipment_item_followers = [x for x in equipment_item_followers if x not in user_followers]
            equipment_dictionary[key]["followers"].extend(equipment_item_followers)

    thumb = image.thumbnail_raw('gallery', None, sync=True)

    if len(user_followers) > 0:
        push_notification(
            user_followers,
            image.user,
            'new_image',
            {
                'image': image,
                'image_thumbnail': thumb.url if thumb else None
            }
        )
    else:
        logger.info('push_notification_for_new_image called for image %d whose author %d has no followers' % (
            image.pk, image.user.pk)
        )

    for key in equipment_dictionary.keys():
        equipment_item = equipment_dictionary[key]['item']
        followers = equipment_dictionary[key]['followers']
        if len(followers) > 0:
            push_notification(
                followers,
                image.user,
                'new-image-from-equipment-item',
                {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None,
                    'item_name': str(equipment_item),
                    'item_url': AppRedirectionService.redirect(
                        f'/equipment/explorer/{equipment_item.klass.lower()}/{equipment_item.id}/{equipment_item.slug}'
                    ),
                }
            )

    else:
        logger.info(
            'push_notification_for_new_image called for image %d whose equipment items have no followers' % image.pk)


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

    user_pks = [revision.image.user.pk] + list(revision.image.collaborators.all().values_list('pk', flat=True))

    followers = [x.user for x in ToggleProperty.objects.filter(
        property_type="follow",
        content_type=ContentType.objects.get_for_model(User),
        object_id__in=user_pks).order_by('object_id')]

    if len(followers) > 0:
        previous_revision = ImageRevision.objects \
            .filter(image=revision.image) \
            .exclude(pk=revision.pk) \
            .order_by('-uploaded').first()

        thumb = revision.thumbnail_raw('gallery', sync=True)

        push_notification(followers, revision.image.user, 'new_image_revision', {
            'url': build_notification_url(settings.BASE_URL + revision.get_absolute_url(), revision.image.user),
            'user_url': build_notification_url(
                settings.BASE_URL + revision.image.user.userprofile.get_absolute_url(), revision.image.user),
            'user': revision.image.user.userprofile.get_display_name(),
            'image_title': revision.image.title,
            'title': revision.title,
            'description': revision.description,
            'previous_update_date': formats.date_format(max(
                revision.image.published,
                previous_revision.uploaded if previous_revision is not None else datetime.min
            ), "DATE_FORMAT"),
            'image_thumbnail': thumb.url if thumb else None,
        })
    else:
        logger.info(
            'push_notification_for_new_image called for revision %d whose author has no followers' % revision_pk
        )


@shared_task(time_limit=300, acks_late=True)
def clear_old_bouncy_objects():
    Delivery.objects.filter(created_at__lte=DateTimeService.now() - timedelta(7)).delete()
    Bounce.objects.filter(created_at__lte=DateTimeService.now() - timedelta(30)).delete()
    Complaint.objects.filter(created_at__lte=DateTimeService.now() - timedelta(90)).delete()
