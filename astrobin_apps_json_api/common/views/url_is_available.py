import logging

import requests
from braces.views import JSONResponseMixin
from django.views.generic.base import View

log = logging.getLogger('apps')


class UrlIsAvailable(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        url = request.GET.get('url')
        available = False

        if url:
            if not '://' in url:
                url = f'http://{url}'
            try:
                requests.get(url, timeout=5)
                available = True
            except requests.ConnectionError:
                pass

        return self.render_json_response({'available': available})
