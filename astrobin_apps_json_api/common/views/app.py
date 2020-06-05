import hashlib
from os.path import join

from braces.views import JSONResponseMixin
from django.core.cache import cache
from django.views.generic.base import View

from astrobin import settings
from common.utils import get_project_root


class AppConfig(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        return self.render_json_response({
            u"version": self.__get_version__(),
            u"i18nHash": self.__get_i18n_hash__(),
        })

    def __get_version__(self):
        # type: () -> str
        version_file = join(get_project_root(), 'VERSION')  # type: str

        f = open(version_file, 'r')  # type: BinaryIO
        version = f.read().strip()  # type: str
        f.close()

        return version

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
