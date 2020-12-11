from rest_framework import serializers

from astrobin_apps_payments.models import ExchangeRate


class ExchangeRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExchangeRate
        fields = (
            'source',
            'target',
            'rate',
            'time'
        )
