from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Filter


class FilterSerializer(GearSerializer):
    class Meta:
        model = Filter
        fields = GearSerializer.Meta.fields + (
            'type',
            'bandwidth',
        )
