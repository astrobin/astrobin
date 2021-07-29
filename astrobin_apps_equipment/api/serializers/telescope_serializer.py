from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Telescope


class TelescopeSerializer(EquipmentItemSerializer, serializers.ModelSerializer):
    class Meta:
        model = Telescope
        fields = '__all__'
