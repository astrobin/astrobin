from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Accessory


class AccessorySerializer(GearSerializer):
    class Meta:
        model = Accessory
