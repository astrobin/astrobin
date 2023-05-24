import logging
from typing import Optional

from braces.views import JSONResponseMixin
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.views import View
from rest_framework.authtoken.models import Token

from astrobin.utils import get_client_country_code
from astrobin_apps_payments.services.pricing_service import PricingService
from astrobin_apps_payments.types import SubscriptionRecurringUnit
from astrobin_apps_premium.services.premium_service import SubscriptionDisplayName

log = logging.getLogger(__name__)


class PricingView(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        product: SubscriptionDisplayName = SubscriptionDisplayName.from_string(kwargs.pop('product', None))
        currency: str = kwargs.pop('currency', None)
        recurring_unit: Optional[SubscriptionRecurringUnit] = SubscriptionRecurringUnit.from_string(kwargs.pop('recurring_unit', None))
        country_code = get_client_country_code(request)

        if product is None or product not in (
                SubscriptionDisplayName.LITE,
                SubscriptionDisplayName.PREMIUM,
                SubscriptionDisplayName.ULTIMATE
        ):
            log.error('pricing_view: invalid product: %s' % product)
            return HttpResponseBadRequest("Invalid product")

        if currency is None or currency.upper() not in settings.SUPPORTED_CURRENCIES:
            log.error('pricing_view: invalid currency: %s' % currency)
            return HttpResponseBadRequest("Unsupported currency")

        user = request.user
        if not user.is_authenticated and 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            token = Token.objects.get(key=token_in_header)
            user = token.user

        return self.render_json_response(
            {
                'fullPrice': PricingService.get_full_price(product, country_code, currency.upper(), recurring_unit),
                'discount': PricingService.get_discount_amount(product, country_code, currency.upper(), recurring_unit, user=user),
                'price': PricingService.get_price(product, country_code, currency.upper(), recurring_unit, user=user)
            }
)
