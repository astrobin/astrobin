from django.template.loader import render_to_string
import urllib2
import simplejson
from notification import models as notification

def push_notification(recipient, type, data):
    notification.send([recipient], type, data)
    rendered = render_to_string('notification/%s/%s' % (type, 'short.html'), data)
    encoded_data = simplejson.dumps({'message':rendered})

    url = 'http://127.0.0.1/publish?id=notification_' + recipient.username
    try:
        urllib2.urlopen(url, encoded_data);
    except:
        pass

