from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Mount


class MountSerializer(GearSerializer):
    class Meta(GearSerializer.Meta):
        model = Mount
        fields = GearSerializer.Meta.fields + (
            'max_payload',
            'pe',
        )
