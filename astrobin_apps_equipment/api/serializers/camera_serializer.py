from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Camera


class CameraSerializer(EquipmentItemSerializer, serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = '__all__'
