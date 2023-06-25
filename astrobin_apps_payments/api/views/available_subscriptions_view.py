import logging

from braces.views import JSONResponseMixin
from django.http import HttpResponse
from django.views import View
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import APIException

from astrobin_apps_payments.api.serializers import StripeSubscriptionSerializer
from astrobin_apps_payments.services.pricing_service import PricingService

log = logging.getLogger('apps')


class AvailableSubscriptionsView(JSONResponseMixin, View):
    def get(self, request, *args, **kwargs) -> HttpResponse:
        user = request.user
        if not user.is_authenticated and 'HTTP_AUTHORIZATION' in request.META:
            token_in_header = request.META['HTTP_AUTHORIZATION'].replace('Token ', '')
            token = Token.objects.get(key=token_in_header)
            user = token.user

        autorenew_supported = PricingService.non_autorenewing_supported(user)
        subscriptions = StripeSubscriptionSerializer(
            data=PricingService.get_available_subscriptions(user),
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
