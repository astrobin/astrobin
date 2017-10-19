# Python
import simplejson
import urllib2

# Django
from django.conf import settings

# Third party
from gadjo.requestprovider.signals import get_request
from notification import models as notification
from notification.models import get_formatted_messages
from persistent_messages.models import Message
import persistent_messages


def push_notification(recipients, notice_type, data):
    data.update({'notices_url': settings.ASTROBIN_BASE_URL + '/'})

    # Send as email
    notification.send(recipients, notice_type, data)

    # Send as persistent message
    try:
        request = get_request()
    except IndexError:
        # This may happen during unit testing
        return

    messages = get_formatted_messages(['notice.html'],
        notice_type, data)

    for recipient in recipients:
        persistent_messages.add_message(
            request,
            persistent_messages.INFO,
            messages['notice.html'],
            user = recipient)


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
