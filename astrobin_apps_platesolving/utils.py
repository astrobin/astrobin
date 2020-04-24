import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.shortcuts import get_object_or_404

from astrobin_apps_platesolving.models import Solution


class ThumbnailNotReadyException(Exception):
    pass


def get_from_storage(image, alias, revision_label):
    url = image.thumbnail(alias, {'sync': True, 'revision_label': revision_label})

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

    r = requests.get(url, verify=False, allow_redirects=True, headers={'User-Agent': 'Mozilla/5.0'})

    img = NamedTemporaryFile(delete=True)
    img.write(r.content)
    img.flush()
    img.seek(0)

    return File(img)


def get_target(object_id, content_type_id):
    content_type = ContentType.objects.get_for_id(content_type_id)
    manager = content_type.model_class()
    if hasattr(manager, 'objects_including_wip'):
        manager = manager.objects_including_wip
    return get_object_or_404(manager, pk=object_id)


def get_solution(object_id, content_type_id):
    content_type = ContentType.objects.get_for_id(content_type_id)
    solution, created = Solution.objects.get_or_create(object_id=object_id, content_type=content_type)
    return solution


def corrected_pixscale(solution, pixscale):
    # type: (Solution, float) -> float
    if solution.content_object:
        w = solution.content_object.w  # type: int
        if w and pixscale:
            hd_w = min(w, settings.THUMBNAIL_ALIASES['']['hd']['size'][0]) # type: int
            ratio = hd_w / float(w)
            return float(pixscale) * ratio
        return pixscale
    return pixscale
