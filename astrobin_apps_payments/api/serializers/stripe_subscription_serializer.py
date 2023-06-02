from rest_framework import serializers
from rest_framework.exceptions import MethodNotAllowed

from astrobin_apps_payments.types import StripeSubscription


class StripeSubscriptionSerializer(serializers.Serializer):
    name = serializers.CharField()
    displayName = serializers.CharField()

    def create(self, validated_data):
        raise MethodNotAllowed('POST')

    def update(self, instance, validated_data):
        raise MethodNotAllowed('PUT')

    def to_internal_value(self, data: StripeSubscription):
        return {
            'name': data.name.value,
            'displayName': data.display_name.value,
        }
