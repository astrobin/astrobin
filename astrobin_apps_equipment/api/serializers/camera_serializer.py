from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.services.camera_service import CameraService


class CameraSerializer(EquipmentItemSerializer):
    modified = serializers.BooleanField(required=False, default=False)

    def validate(self, attrs):
        CameraService.validate(attrs)
        return super().validate(attrs)

    class Meta(EquipmentItemSerializer.Meta):
        model = Camera
        fields = '__all__'
        abstract = False
