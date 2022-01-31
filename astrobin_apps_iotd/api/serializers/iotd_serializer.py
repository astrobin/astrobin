from datetime import date, timedelta

from rest_framework import serializers

from astrobin_apps_iotd.models import Iotd


class IotdSerializer(serializers.ModelSerializer):
    date = serializers.DateField(required=False)

    def create(self, validated_data):
        if 'judge' not in validated_data:
            validated_data['judge'] = self.context['request'].user

        day = date.today()
        while self.Meta.model.objects.filter(date=day).exists():
            day = day + timedelta(1)

        validated_data['date'] = day

        return super().create(validated_data)

    class Meta:
        model = Iotd
        fields = (
            'id',
            'judge',
            'image',
            'date',
        )
