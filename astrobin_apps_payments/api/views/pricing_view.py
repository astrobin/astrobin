import logging

from braces.views import JSONResponseMixin
from django.conf import settings
from django.http import HttpResponseBadRequest
from django.views import View
from rest_framework.authtoken.models import Token

from astrobin_apps_payments.services.pricing_service import PricingService

log = logging.getLogger('apps')

class PricingView(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs):
        product = kwargs.pop('product', None)  # type: str
        currency = kwargs.pop('currency', None)  # type: str

        if product is None or product.lower() not in ('lite', 'premium', 'ultimate'):
            log.error('pricing_view: invalid product: %s' % product)
            return HttpResponseBadRequest("Invalid product")

        if currency is None or currency.upper() not in settings.SUPPORTED_CURRENCIES:
            log.error('pricing_view: invalid currency: %s' % currency)
            return HttpResponseBadRequest("Unsupported currency")

        user = None
        if 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            token = Token.objects.get(key=token_in_header)
            user = token.user

        return self.render_json_response({
            'fullPrice': PricingService.get_full_price(product.lower(), currency.upper()),
            'discount': PricingService.get_discount_amount(product.lower(), currency.upper(), user=user),
            'price': PricingService.get_price(product.lower(), currency.upper(), user=user)
        })

