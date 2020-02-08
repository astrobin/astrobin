import requests
from django.conf import settings
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile


class ThumbnailNotReadyException(Exception):
    pass


def getFromStorage(image, alias):
    url = image.thumbnail(alias)

    if "placeholder" in url:
        raise ThumbnailNotReadyException

    if settings.MEDIA_URL not in url:
        media_url = settings.MEDIA_URL
        if media_url.endswith('/'):
            media_url = media_url[:-1]

        last_part_of_media = media_url.rsplit('/', 1)[-1]
        first_part_of_url = url.strip('/').split('/')[0]

        if (last_part_of_media == first_part_of_url):
            media_url = media_url.strip(last_part_of_media).strip('/')

        url = media_url + url

    r = requests.get(url, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})

    img = NamedTemporaryFile(delete=True)
    img.write(r.content)
    img.flush()
    img.seek(0)

    return File(img)
