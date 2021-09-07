from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.models import Camera


class CameraSerializer(GearSerializer):
    class Meta:
        model = Camera
        fields = GearSerializer.Meta.fields + (
            'pixel_size',
            'sensor_width',
            'sensor_height',
            'type'
        )
