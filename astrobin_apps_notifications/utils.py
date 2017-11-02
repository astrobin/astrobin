# Python
import simplejson
import urllib2

# Django
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.utils.translation import get_language, activate

# Third party
from gadjo.requestprovider.signals import get_request
from notification import models as notification
from persistent_messages.models import Message
import persistent_messages


def push_notification(recipients, notice_type, data):
    data.update({'notices_url': settings.ASTROBIN_BASE_URL})

    # Send as email
    notification.send(recipients, notice_type, data)

    # Send as persistent message
    try:
        request = get_request()
    except IndexError:
        # This may happen during unit testing
        return

    def get_notification_language(user):
        if getattr(settings, "NOTIFICATION_LANGUAGE_MODULE", False):
            try:
                app_label, model_name = settings.NOTIFICATION_LANGUAGE_MODULE.split(".")
                model = apps.get_model(app_label, model_name)
                # pylint: disable-msg=W0212
                language_model = model._default_manager.get(user__id__exact=user.id)
                if hasattr(language_model, "language"):
                    return language_model.language
            except (ImportError, ImproperlyConfigured):
                return None
        return None

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

    current_language = get_language()

    for recipient in recipients:
        language = get_notification_language(recipient)
        if language:
            activate(language)
        messages = get_formatted_messages(['notice.html'], notice_type, data)
        persistent_messages.add_message(
            request,
            persistent_messages.INFO,
            messages['notice.html'],
            user = recipient)

    activate(current_language)


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
