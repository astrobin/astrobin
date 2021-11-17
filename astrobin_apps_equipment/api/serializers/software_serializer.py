from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Software


class SoftwareSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Software
        fields = '__all__'
        abstract = False
