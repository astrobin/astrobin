from django.template.loader import render_to_string
import urllib2
import simplejson
from notification import models as notification

def push_notification(recipients, type, data):
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

