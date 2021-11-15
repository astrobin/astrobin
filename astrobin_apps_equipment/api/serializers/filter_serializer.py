from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Filter


class FilterSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Filter
        fields = '__all__'
        abstract = False
