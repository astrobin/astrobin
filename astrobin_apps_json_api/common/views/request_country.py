import logging

from braces.views import JSONResponseMixin
from django.views.generic.base import View

from astrobin import utils

log = logging.getLogger(__name__)


class RequestCountry(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        return self.render_json_response(
            {
                'country': utils.get_client_country_code(request),
            }
        )
