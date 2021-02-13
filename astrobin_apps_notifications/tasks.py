from celery import shared_task
from django.core.management import call_command

from astrobin.models import UserProfile, Image
from astrobin_apps_notifications.utils import push_notification
from toggleproperties.models import ToggleProperty


@shared_task()
def purge_old_notifications():
    call_command("purge_old_notifications")


@shared_task()
def push_notification_for_new_image(user_pk, image_pk):
    try:
        image = Image.objects_including_wip.get(pk=image_pk)
    except Image.DoesNotExist:
        return

    if image.is_wip:
        return

    followers = [
        x.user for x in
        ToggleProperty.objects.toggleproperties_for_object(
            "follow",
            UserProfile.objects.get(user__pk=user_pk).user)
    ]

    if len(followers) > 0:
        thumb = image.thumbnail_raw('gallery', None, sync=True)
        push_notification(followers, 'new_image', {
            'image': image,
            'image_thumbnail': thumb.url if thumb else None
        })
