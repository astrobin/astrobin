from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Camera


class CameraSerializer(EquipmentItemSerializer):
    modified = serializers.BooleanField(required=False, default=False)

    class Meta(EquipmentItemSerializer.Meta):
        model = Camera
        fields = '__all__'
        abstract = False
