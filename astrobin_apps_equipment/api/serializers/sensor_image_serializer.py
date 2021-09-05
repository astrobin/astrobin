from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models import Sensor


class SensorImageSerializer(EquipmentItemImageSerializer, serializers.ModelSerializer):
    class Meta:
        model = Sensor
        fields = EquipmentItemImageSerializer.Meta.fields
