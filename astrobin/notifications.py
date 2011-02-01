from django.template.loader import render_to_string
from django.conf import settings
import urllib2
import simplejson
from notification import models as notification

def push_notification(recipients, type, data):
    data['notices_url'] = settings.ASTROBIN_SHORT_BASE_URL + '/notifications/'
    notification.send(recipients, type, data)
    rendered = render_to_string('notification/%s/%s' % (type, 'short.html'), data)
    encoded_data = simplejson.dumps({'message':rendered})

    for r in recipients:
        url = 'http://127.0.0.1/publish?id=notification_' + r.username
        try:
            urllib2.urlopen(url, encoded_data);
        except:
            pass


def push_message(recipient, data):
    encoded_data = simplejson.dumps(data)
    url = 'http://127.0.0.1/publish?id=message_' + recipient.username
    try:
        urllib2.urlopen(url, encoded_data);
    except:
        pass


def push_request(recipient, request):
    encoded_data = simplejson.dumps({'image_id':request.image.id})
    url = 'http://127.0.0.1/publish?id=request_' + recipient.username
    try:
        urllib2.urlopen(url, encoded_data);
    except:
        pass

