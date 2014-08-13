import simplejson
import urllib2

from django.conf import settings
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils import translation

from gadjo.requestprovider.signals import get_request
from notification import models as notification
import persistent_messages

def push_notification(recipients, notice_type, data):
    current_language = translation.get_language()

    data['notices_url'] = settings.ASTROBIN_BASE_URL + '/'

    try:
        notification.send(recipients, notice_type, data)
    except:
        pass

    try:
        request = get_request()
    except IndexError:
        # This may happen during test cases
        return

    for r in recipients:
        language = r.userprofile.language

        if language is not None:
            if language == 'pl':
                # Polish is currently broken...
                language = 'en'
            translation.activate(language)

        notification_message = render_to_string(
            'notification/%s/%s' % (notice_type, 'short.html'),
             data)

        persistent_messages.add_message(
            request,
            persistent_messages.INFO,
            notification_message,
            user = r)

        if settings.LONGPOLL_ENABLED:
            encoded_data = simplejson.dumps({'message': notification_message})
            url = 'http://127.0.0.1/publish?id=notification_' + r.username
            try:
                urllib2.urlopen(url, encoded_data);
            except:
                pass

    translation.activate(current_language)

