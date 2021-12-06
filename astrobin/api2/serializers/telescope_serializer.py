from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Telescope


class TelescopeSerializer(GearSerializer):
    class Meta(GearSerializer.Meta):
        model = Telescope
        fields = GearSerializer.Meta.fields + (
            'aperture',
            'focal_length',
            'type',
        )
