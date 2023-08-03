import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.utils import formats
from django_bouncy.models import Bounce, Complaint, Delivery

from astrobin.models import Image, ImageRevision
from astrobin_apps_notifications.utils import build_notification_url, push_notification
from common.services import DateTimeService
from toggleproperties.models import ToggleProperty

logger = logging.getLogger(__name__)


@shared_task(time_limit=300)
def purge_old_notifications():
    call_command("purge_old_notifications")


@shared_task(time_limit=300)
def push_notification_for_approved_image(image_pk: int, moderator_pk: int):
    try:
        image = Image.objects_including_wip.get(pk=image_pk)
    except Image.DoesNotExist:
        logger.error('push_notification_for_approved_image called for image not found: %d' % image_pk)
        return

    try:
        moderator = User.objects.get(pk=moderator_pk)
    except User.DoesNotExist:
        logger.error('push_notification_for_approved_image called for moderator not found: %d' % moderator_pk)
        return

    thumb = image.thumbnail_raw('gallery', None, sync=True)

    push_notification(
        [image.user],
        moderator,
        'image_approved',
        {
            'image': image,
            'image_thumbnail': thumb.url if thumb else None,
            'moderator': moderator
        }
    )


@shared_task(time_limit=1800)
def push_notification_for_new_image(image_pk: int):
    try:
        image = Image.objects_including_wip.get(pk=image_pk)
    except Image.DoesNotExist:
        logger.error('push_notification_for_new_image called for image not found: %d' % image_pk)
        return

    if image.is_wip:
        logger.error('push_notification_for_new_image called for image that is wip: %d' % image_pk)
        return

    def get_image_followers():
        user_pks = [image.user.pk] + list(image.collaborators.all().values_list('pk', flat=True))

        return list(set([x.user for x in ToggleProperty.objects.filter(
            property_type="follow",
            content_type=ContentType.objects.get_for_model(User),
            object_id__in=user_pks
        ).order_by('object_id')]))


    def get_image_group_followers():
        all_groups = image.part_of_group_set.all()
        all_users = []
        for group in all_groups:
            all_users.extend([group.owner])
            all_users.extend(group.members.all())
        return list(set(all_users))
        
        
        
    def get_equipment_dictionary():
        """
        Returns a dictionary of equipment items and their followers, like this:
        {
            'telescope-1': {
                'item': <Telescope: 1>,
                'followers': [<User: 1>, <User: 2>]
            },
            'camera-1': {
                'item': <Camera: 1>,
                'followers': [<User: 1>, <User: 3>]
            },
        }
        """
        val = {}

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
                if key not in val:
                    val[key] = {"item": equipment_item, "followers": []}

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

                val[key]["followers"].extend(equipment_item_followers)
                val[key]["followers"] = list(set(val[key]["followers"]))

        return val

    def get_user_equipment_dictionary():
        """
        Returns a dictionary of users and their equipment items, like this:
        {
            1: {
                'user': <User: 1>,
                'items': [<Telescope: 1>, <Camera: 1>]
            },
            2: {
                'user': <User: 2>,
                'items': [<Telescope: 1>]
            },
            3: {
                'user': <User: 3>,
                'items': [<Camera: 1>]
            },
        }
        """
        val = {}

        for key in equipment_dictionary.keys():
            equipment_item = equipment_dictionary[key]['item']
            followers = equipment_dictionary[key]['followers']
            if len(followers) > 0:
                for x in followers:
                    if x.pk not in val:
                        val[x.pk] = {'user': x, 'items': []}
                    val[x.pk]['items'].append(equipment_item)

        return val

    user_followers = get_image_followers()
    user_group_followers = [user for user in get_image_group_followers() if user not in user_followers]
    equipment_dictionary = get_equipment_dictionary()
    user_equipment_dictionary = get_user_equipment_dictionary()
    thumb = image.thumbnail_raw('gallery', None, sync=True)
    new_image_sent_to = []

    if len(user_followers) > 0:
        for follower in user_followers:
            new_image_sent_to.append(follower)
            push_notification(
                [follower],
                image.user,
                'new_image',
                {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None,
                    'followed_equipment_items': user_equipment_dictionary[follower.pk]['items']
                    if follower.pk in user_equipment_dictionary else [],
                }
            )
    else:
        logger.info(
            'push_notification_for_new_image called for image %d whose author %d has no followers' % (
                image.pk, image.user.pk)
        )

        for follower in user_group_followers:
            if follower not in new_image_sent_to:           
                new_image_sent_to.append(follower)
                push_notification(
                    [follower],
                    image.user,
                    'new_image_in_group',
                    {
                        'image': image,
                        'image_thumbnail': thumb.url if thumb else None,
                        'followed_equipment_items': user_equipment_dictionary[follower.pk]['items']
                        if follower.pk in user_equipment_dictionary else [],
                    }
                )

    for key in user_equipment_dictionary.keys():
        follower = user_equipment_dictionary[key]['user']
        equipment_items = user_equipment_dictionary[key]['items']
        if follower not in new_image_sent_to:
            push_notification(
                [follower],
                image.user,
                'new-image-from-followed-equipment',
                {
                    'image': image,
                    'image_thumbnail': thumb.url if thumb else None,
                    'items': equipment_items
                }
            )
    else:
        logger.info(
            'push_notification_for_new_image called for image %d whose equipment items have no followers' % image.pk
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
