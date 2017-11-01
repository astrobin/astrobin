# Python
import simplejson
import urllib2

# Django
from django.conf import settings
from django.template.loader import render_to_string

# Third party
from gadjo.requestprovider.signals import get_request
from notification import models as notification
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

    def get_formatted_messages(formats, label, context):
        """
        Returns a dictionary with the format identifier as the key. The values are
        are fully rendered templates with the given context.
        """
        format_templates = {}
        for fmt in formats:
            # conditionally turn off autoescaping for .txt extensions in format
            if fmt.endswith(".txt"):
                context.autoescape = False
            format_templates[fmt] = render_to_string((
                "notification/%s/%s" % (label, fmt),
                "notification/%s" % fmt), context=context)
        return format_templates

    messages = get_formatted_messages(['notice.html'], notice_type, data)

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
