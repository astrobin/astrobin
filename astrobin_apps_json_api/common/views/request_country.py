import logging

from braces.views import JSONResponseMixin
from django.http import HttpResponse
from django.views.generic.base import View

from astrobin import utils

log = logging.getLogger(__name__)


class RequestCountry(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        country_code: str = utils.get_client_country_code(request)
        currency_code: str = utils.get_currency_code(country_code)

        return self.render_json_response(
            {
                'country': country_code,
                'currency': currency_code,
            }
        )
