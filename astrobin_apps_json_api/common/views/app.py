import hashlib
from os.path import join

from PIL import Image as PILImage
from braces.views import JSONResponseMixin
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.views.generic.base import View

from astrobin import utils
from astrobin.models import Image
from common.utils import get_project_root


class AppConfig(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        return self.render_json_response({
            u"i18nHash": self.__get_i18n_hash__(),
            u"readOnly": self.__get_read_only_mode__(),
            u"PREMIUM_MAX_IMAGES_FREE": settings.PREMIUM_MAX_IMAGES_FREE,
            u"PREMIUM_MAX_IMAGES_LITE": settings.PREMIUM_MAX_IMAGES_LITE,
            u"PREMIUM_MAX_IMAGES_FREE_2020": settings.PREMIUM_MAX_IMAGES_FREE_2020,
            u"PREMIUM_MAX_IMAGES_LITE_2020": settings.PREMIUM_MAX_IMAGES_LITE_2020,
            u"PREMIUM_MAX_IMAGES_PREMIUM_2020": settings.PREMIUM_MAX_IMAGES_PREMIUM_2020,
            u"PREMIUM_MAX_IMAGE_SIZE_FREE_2020": settings.PREMIUM_MAX_IMAGE_SIZE_FREE_2020,
            u"PREMIUM_MAX_IMAGE_SIZE_LITE_2020": settings.PREMIUM_MAX_IMAGE_SIZE_LITE_2020,
            u"PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020": settings.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020,
            u"PREMIUM_MAX_REVISIONS_FREE_2020": settings.PREMIUM_MAX_REVISIONS_FREE_2020,
            u"PREMIUM_MAX_REVISIONS_LITE_2020": settings.PREMIUM_MAX_REVISIONS_LITE_2020,
            u"PREMIUM_MAX_REVISIONS_PREMIUM_2020": settings.PREMIUM_MAX_REVISIONS_PREMIUM_2020,
            u"PREMIUM_PRICE_FREE_2020": settings.PREMIUM_PRICE_FREE_2020,
            u"PREMIUM_PRICE_LITE_2020": settings.PREMIUM_PRICE_LITE_2020,
            u"PREMIUM_PRICE_PREMIUM_2020": settings.PREMIUM_PRICE_PREMIUM_2020,
            u"PREMIUM_PRICE_ULTIMATE_2020": settings.PREMIUM_PRICE_ULTIMATE_2020,
            u"MAX_IMAGE_PIXELS": PILImage.MAX_IMAGE_PIXELS,
            u"GOOGLE_ADS_ID": settings.GOOGLE_ADS_ID,
            u"REQUEST_COUNTRY": utils.get_client_country_code(request),
            u"IMAGE_CONTENT_TYPE_ID": ContentType.objects.get_for_model(Image).id,
            u"THUMBNAIL_ALIASES": settings.THUMBNAIL_ALIASES[''],
            u"IOTD_SUBMISSION_MAX_PER_DAY": settings.IOTD_SUBMISSION_MAX_PER_DAY,
            u"IOTD_REVIEW_MAX_PER_DAY": settings.IOTD_REVIEW_MAX_PER_DAY,
        })

    def __get_i18n_hash__(self):
        cache_key = "astrobin_i18n_hash"
        digest = cache.get(cache_key)
        if digest is not None:
            return digest

        hashes = []  # type: List[str]
        project_root = get_project_root()  # type: str

        for language in [x[0] for x in settings.LANGUAGES]:  # type: str
            for app in ['astrobin'] + settings.ASTROBIN_APPS:  # type: str
                po_file = join(project_root, app, 'locale', language, 'LC_MESSAGES', 'django.po')  # type: str
                language_app_md5 = hashlib.md5()
                try:
                    with open(po_file, "r") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            language_app_md5.update(chunk)
                    hashes.append(language_app_md5.hexdigest())
                except IOError:
                    continue

        total_md5 = hashlib.md5()
        total_md5.update(str(hashes))
        digest = total_md5.hexdigest()

        cache.set(cache_key, digest, 3600)

        return digest

    def __get_read_only_mode__(self):
        return settings.READONLY_MODE
