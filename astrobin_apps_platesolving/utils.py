# Python
import urllib2

# Django
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


def getFromStorage(image, alias):
    url = image.thumbnail(alias)
    if "://" in url:
        url = url.split('://')[1]
    else:
        url = settings.BASE_URL + url

    url = 'http://' + urllib2.quote(url.encode('utf-8'))
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request(url, None, headers)
    img = NamedTemporaryFile(delete = True)
    img.write(urllib2.urlopen(req).read())
    img.flush()
    img.seek(0)
    return File(img)
