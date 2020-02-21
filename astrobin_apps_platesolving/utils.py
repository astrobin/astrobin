import urllib2
from urlparse import urlparse

from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


class ThumbnailNotReadyException(Exception):
    pass


def getFromStorage(image, alias, revision_label):
    url = image.thumbnail(alias, {'revision_label': revision_label, 'sync': True})

    if "placeholder" in url:
        raise ThumbnailNotReadyException

    if not settings.AWS_S3_ENABLED:
        url = settings.BASE_URL + url

    parsed = urlparse(url)
    url = "%s://%s%s" % (parsed.scheme, parsed.netloc, urllib2.quote(parsed.path.encode('utf-8')))

    headers = {'User-Agent': 'Mozilla/5.0'}
    req = urllib2.Request(url, None, headers)
    img = NamedTemporaryFile(delete=True)
    img.write(urllib2.urlopen(req).read())
    img.flush()
    img.seek(0)

    return File(img)
