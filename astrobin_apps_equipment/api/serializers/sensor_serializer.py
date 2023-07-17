from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer

from astrobin_apps_equipment.models import Camera, Sensor


class SensorSerializer(EquipmentItemSerializer):

    cameras = serializers.SerializerMethodField(read_only=True)

    def get_cameras(self, item):
        return Camera.objects.filter(sensor=item.id).values_list('pk', flat=True).order_by('-user_count')

    class Meta:
        model = Sensor
        fields = '__all__'
        abstract = False
