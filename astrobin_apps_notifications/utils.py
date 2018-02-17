# Python
import simplejson
import urllib2

# Django
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

# Third party
from notification import models as notification
from persistent_messages.models import Message


def push_notification(recipients, notice_type, data):
    data.update({'notices_url': settings.BASE_URL + '/'})
    notification.send(recipients, notice_type, data)


def get_recent_notifications(user, n = 10):
    if not user.is_authenticated():
        return None

    notifications = Message.objects.filter(user = user).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications


def get_unseen_notifications(user, n = 10):
    if not user.is_authenticated():
        return None

    notifications =\
        Message.objects.filter(user = user, read = False).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications


def get_seen_notifications(user, n = 10):
    if not user.is_authenticated():
        return None

    notifications =\
        Message.objects.filter(user = user, read = True).order_by('-created')
    if n >= 0:
        notifications = notifications[:n]
    return notifications
