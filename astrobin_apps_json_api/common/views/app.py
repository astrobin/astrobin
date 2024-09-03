import hashlib
import logging
import os
from os.path import join

from PIL import Image as PILImage
from braces.views import JSONResponseMixin
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.views.generic.base import View

from astrobin import utils
from astrobin.models import Image
from common.utils import get_project_root, read_in_chunks

log = logging.getLogger(__name__)


@method_decorator([cache_page(3600), vary_on_headers('Cookie', 'Authorization')], name='dispatch')
class AppConfig(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        return self.render_json_response({
            'i18nHash': self.__get_i18n_hash__(),
            'readOnly': self.__get_read_only_mode__(),
            'PREMIUM_MAX_IMAGES_FREE': settings.PREMIUM_MAX_IMAGES_FREE,
            'PREMIUM_MAX_IMAGES_LITE': settings.PREMIUM_MAX_IMAGES_LITE,
            'PREMIUM_MAX_IMAGES_FREE_2020': settings.PREMIUM_MAX_IMAGES_FREE_2020,
            'PREMIUM_MAX_IMAGES_LITE_2020': settings.PREMIUM_MAX_IMAGES_LITE_2020,
            'PREMIUM_MAX_IMAGES_PREMIUM_2020': settings.PREMIUM_MAX_IMAGES_PREMIUM_2020,
            'PREMIUM_MAX_IMAGE_SIZE_FREE_2020': settings.PREMIUM_MAX_IMAGE_SIZE_FREE_2020,
            'PREMIUM_MAX_IMAGE_SIZE_LITE_2020': settings.PREMIUM_MAX_IMAGE_SIZE_LITE_2020,
            'PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020': settings.PREMIUM_MAX_IMAGE_SIZE_PREMIUM_2020,
            'PREMIUM_MAX_REVISIONS_FREE_2020': settings.PREMIUM_MAX_REVISIONS_FREE_2020,
            'PREMIUM_MAX_REVISIONS_LITE_2020': settings.PREMIUM_MAX_REVISIONS_LITE_2020,
            'PREMIUM_MAX_REVISIONS_PREMIUM_2020': settings.PREMIUM_MAX_REVISIONS_PREMIUM_2020,
            'PREMIUM_PRICE_FREE_2020': settings.PREMIUM_PRICE_FREE_2020,
            'PREMIUM_PRICE_LITE_2020': settings.PREMIUM_PRICE_LITE_2020,
            'PREMIUM_PRICE_PREMIUM_2020': settings.PREMIUM_PRICE_PREMIUM_2020,
            'PREMIUM_PRICE_ULTIMATE_2020': settings.PREMIUM_PRICE_ULTIMATE_2020,
            'MAX_IMAGE_PIXELS': PILImage.MAX_IMAGE_PIXELS,
            'MAX_FILE_SIZE': settings.MAX_FILE_SIZE,
            'GOOGLE_ADS_ID': settings.GOOGLE_ADS_ID,
            'REQUEST_COUNTRY': utils.get_client_country_code(request),
            'IMAGE_CONTENT_TYPE_ID': ContentType.objects.get_for_model(Image).id,
            'THUMBNAIL_ALIASES': settings.THUMBNAIL_ALIASES[''],
            'IOTD_SUBMISSION_WINDOW_DAYS': settings.IOTD_SUBMISSION_WINDOW_DAYS,
            'IOTD_SUBMISSION_MAX_PER_DAY': settings.IOTD_SUBMISSION_MAX_PER_DAY,
            'IOTD_SUBMISSION_MIN_PROMOTIONS': settings.IOTD_SUBMISSION_MIN_PROMOTIONS,
            'IOTD_REVIEW_MIN_PROMOTIONS': settings.IOTD_REVIEW_MIN_PROMOTIONS,
            'IOTD_REVIEW_WINDOW_DAYS': settings.IOTD_REVIEW_WINDOW_DAYS,
            'IOTD_REVIEW_MAX_PER_DAY': settings.IOTD_REVIEW_MAX_PER_DAY,
            'IOTD_JUDGEMENT_WINDOW_DAYS': settings.IOTD_JUDGEMENT_WINDOW_DAYS,
            'IOTD_JUDGEMENT_MAX_PER_DAY': settings.IOTD_JUDGEMENT_MAX_PER_DAY,
            'IOTD_JUDGEMENT_MAX_FUTURE_DAYS': settings.IOTD_JUDGEMENT_MAX_FUTURE_DAYS,
            'IOTD_QUEUES_PAGE_SIZE': settings.IOTD_QUEUES_PAGE_SIZE,
            'IOTD_MAX_DISMISSALS': settings.IOTD_MAX_DISMISSALS,
            'IMAGE_UPLOAD_ENDPOINT': '/api/v2/images/image-upload/',
            'IMAGE_REVISION_UPLOAD_ENDPOINT': '/api/v2/images/image-revision-upload/',
            'DATA_UPLOAD_MAX_MEMORY_SIZE': settings.DATA_UPLOAD_MAX_MEMORY_SIZE,
            'STRIPE_CUSTOMER_PORTAL_KEY': settings.STRIPE['keys']['customer-portal-key'],
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

                if not os.path.exists(po_file):
                    continue

                language_app_md5 = hashlib.md5()
                try:
                    with open(po_file, "rb") as f:
                        for chunk in read_in_chunks(f, 4096):
                            language_app_md5.update(chunk)
                    hashes.append(language_app_md5.hexdigest())
                except IOError as e:
                    log.error('IOError while reading PO file %s: %s' % (po_file, str(e)))
                    continue

        total_md5 = hashlib.md5()
        total_md5.update(str(hashes).encode('utf-8'))
        digest = total_md5.hexdigest()

        cache.set(cache_key, digest, 3600)

        return digest

    def __get_read_only_mode__(self):
        return settings.READONLY_MODE
