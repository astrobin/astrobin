import logging

from braces.views import JSONResponseMixin
from django.http import HttpResponse
from django.views import View
from rest_framework.exceptions import APIException

from astrobin_apps_payments.api.serializers import StripeSubscriptionSerializer
from astrobin_apps_payments.services.pricing_service import PricingService

log = logging.getLogger('apps')


class AvailableSubscriptionsView(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        autorenew_supported = PricingService.non_autorenewing_supported(request.user)
        subscriptions = StripeSubscriptionSerializer(
            data=PricingService.get_available_subscriptions(request.user),
            many=True,
        )

        if not subscriptions.is_valid():
            error = str(subscriptions.errors)
            log.error(f'AvailableSubscriptionsView: {error}')
            raise APIException(f'Internal server error: {error}')

        return self.render_json_response(
            {
                'nonAutorenewingSupported': autorenew_supported,
                'subscriptions': subscriptions.data,
            }
        )
