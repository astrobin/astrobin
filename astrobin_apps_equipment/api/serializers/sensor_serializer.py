from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from rest_framework import serializers

from astrobin_apps_equipment.models import Sensor


class SensorSerializer(EquipmentItemSerializer, serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = '__all__'
