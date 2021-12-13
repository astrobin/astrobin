from datetime import timedelta

from rest_framework import serializers

from astrobin_apps_iotd.models import Iotd
from common.services import DateTimeService


class IotdSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False)

    def create(self, validated_data):
        if 'judge' not in validated_data:
            validated_data['judge'] = self.context['request'].user

        latest_iotd = self.Meta.model.objects.first()

        validated_data['date'] = latest_iotd.date + timedelta(1) \
            if latest_iotd \
            else DateTimeService.today()

        return super().create(validated_data)

    class Meta:
        model = Iotd
        fields = (
            'id',
            'judge',
            'image',
            'date',
        )
