import logging

import requests
from braces.views import JSONResponseMixin
from django.views.generic.base import View

from common.tls_adapter import TLSAdapter

log = logging.getLogger(__name__)


class UrlIsAvailable(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        url = request.GET.get('url')
        available = False

        if url:
            if not '://' in url:
                url = f'http://{url}'
            try:
                session = requests.session()
                session.mount('https://', TLSAdapter())
                session.request('HEAD', url, timeout=5, allow_redirects=False)
                available = True
            except requests.ConnectionError as e:
                log.debug(f'Unable to connect to {url}: {str(e)}')

        return self.render_json_response({'available': available})
