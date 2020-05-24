from os.path import abspath, dirname, join

from braces.views import HeaderMixin
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic.base import View

from common.utils import get_project_root


@method_decorator(cache_page(60*60*24*30), name='dispatch')
class I18nMessages(HeaderMixin, View):
    headers = {
        'Content-Type': 'text/plain'
    }

    def get(self, request, *args, **kwargs):
        code = kwargs.pop('code', 'en')  # type: str

        if code not in [x[0] for x in settings.LANGUAGES]:
            code = 'en'

        cache_key = "astrobin_i18n_messages_%s" % code
        content = cache.get(cache_key)
        if content is not None:
            return HttpResponse(content)

        project_root = get_project_root()  # type: str

        content = ''

        for app in ['astrobin'] + settings.ASTROBIN_APPS:
            po_file = join(project_root, app, 'locale', code, 'LC_MESSAGES', 'django.po')  # type: str

            try:
                with open(po_file, 'r') as f:
                    for i, line in enumerate(f):
                        if not line.startswith('#'):
                            content += line
            except IOError:
                continue

        cache.set(cache_key, content, 3600)

        return HttpResponse(content)
