# Python
import urllib2

# Django
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


def getFromStorage(image, alias):
    def encoded(path):
        return urllib2.quote(path.encode('utf-8'))

    url = image.thumbnail(alias)

    if "://" in url:
        # We are getting the full path and must only encode the part after the protocol
        # (we assume that the hostname is ASCII)
        protocol, path = url.split("://")
        url = protocol + encoded(path)
    else:
        url = settings.BASE_URL + encoded(url)

    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request(url, None, headers)
    img = NamedTemporaryFile(delete = True)
    img.write(urllib2.urlopen(req).read())
    img.flush()
    img.seek(0)
    return File(img)
