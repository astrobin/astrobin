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
    data['notices_url'] = settings.ASTROBIN_BASE_URL + '/'
    data['LANGUAGE_CODE'] = translation.get_language()
    try:
        notification.send(recipients, notice_type, data)
    except:
        pass

    notification_message = render_to_string(
        'notification/%s/%s' % (notice_type, 'short.html'),
         data)

    request = get_request()

    for r in recipients:
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

