import logging

from celery import shared_task
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse

from astrobin_apps_groups.models import Group
from astrobin_apps_notifications.utils import push_notification, build_notification_url

logger = logging.getLogger('apps')

@shared_task(time_limit=120)
def push_notification_for_group_join_request_approval(group_pk, user_pk, moderator_pk):
    try:
        group = Group.objects.get(pk=group_pk)
    except Group.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_approval: group not found: %d' % group_pk)
        return

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_approval: user not found: %d' % user_pk)
        return

    try:
        moderator = User.objects.get(pk=moderator_pk)
    except User.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_approval: moderator not found: %d' % moderator_pk)
        return

    push_notification(
        [user], moderator, 'group_join_request_approved',
        {
            'group_name': group.name,
            'url': build_notification_url(
                settings.BASE_URL + reverse('group_detail', args=(group.pk,)), moderator
            ),
        })


@shared_task(time_limit=120)
def push_notification_for_group_join_request_rejection(group_pk, user_pk, moderator_pk):
    try:
        group = Group.objects.get(pk=group_pk)
    except Group.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_rejection: group not found: %d' % group_pk)
        return

    try:
        user = User.objects.get(pk=user_pk)
    except User.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_rejection: user not found: %d' % user_pk)
        return

    try:
        moderator = User.objects.get(pk=moderator_pk)
    except User.DoesNotExist:
        logger.warning('push_notification_for_group_join_request_rejection: moderator not found: %d' % moderator_pk)
        return

    push_notification(
        [user], moderator, 'group_join_request_rejected',
        {
            'group_name': group.name,
            'url': build_notification_url(
                settings.BASE_URL + reverse('group_detail', args=(group.pk,)), moderator
            ),
        })

