from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer

from astrobin_apps_equipment.models import Sensor


class SensorSerializer(EquipmentItemSerializer):
    class Meta:
        model = Sensor
        fields = '__all__'
        abstract = False
