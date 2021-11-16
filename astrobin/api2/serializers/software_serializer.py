from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Software


class SoftwareSerializer(GearSerializer):
    class Meta:
        model = Software
