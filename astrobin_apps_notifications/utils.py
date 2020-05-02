from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

from notification import models as notification
from persistent_messages.models import Message


def clear_notifications_template_cache(username):
    key = make_template_fragment_key('notifications_table', [username])
    cache.delete(key)


def push_notification(recipients, notice_type, data):
    data.update({
        'notices_url': settings.BASE_URL + '/',
        'base_url': settings.BASE_URL,
    })
    notification.send(recipients, notice_type, data)
    for recipient in recipients:
        clear_notifications_template_cache(recipient.username)


def get_recent_notifications(user, n=10):
    if not user.is_authenticated():
        return None

    notifications = Message.objects.filter(user=user).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications


def get_unseen_notifications(user, n=10):
    if not user.is_authenticated():
        return None

    notifications = \
        Message.objects.filter(user=user, read=False).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications


def get_seen_notifications(user, n=10):
    if not user.is_authenticated():
        return None

    notifications = \
        Message.objects.filter(user=user, read=True).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications
