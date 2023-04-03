from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed

from astrobin_apps_payments.types import StripeSubscription


class StripeSubscriptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    product_id = serializers.CharField()
    yearly_price_id = serializers.CharField(required=False)
    monthly_price_id = serializers.CharField()

    def create(self, validated_data):
        raise MethodNotAllowed('POST')

    def update(self, instance, validated_data):
        raise MethodNotAllowed('PUT')

    def to_internal_value(self, data: StripeSubscription):
        return {
            'name': data.name.value,
            'product_id': data.product_id,
            'yearly_price_id': data.yearly_price_id,
            'monthly_price_id': data.monthly_price_id,
        }
