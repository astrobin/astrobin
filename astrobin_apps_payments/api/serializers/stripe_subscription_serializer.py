from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed

from astrobin_apps_payments.types import StripeSubscription


class StripeSubscriptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    displayName = serializers.CharField()
    productId = serializers.CharField()
    yearlyPriceId = serializers.CharField(required=False)
    monthlyPriceId = serializers.CharField()

    def create(self, validated_data):
        raise MethodNotAllowed('POST')

    def update(self, instance, validated_data):
        raise MethodNotAllowed('PUT')

    def to_internal_value(self, data: StripeSubscription):
        return {
            'name': data.name.value,
            'displayName': data.display_name.value,
            'productId': data.product_id,
            'yearlyPriceId': data.yearly_price_id,
            'monthlyPriceId': data.monthly_price_id,
        }
