from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Filter


class FilterSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Filter
        fields = '__all__'
        abstract = False


class FilterSerializerForImage(FilterSerializer):
    class Meta(FilterSerializer.Meta):
        fields = (
            'id',
            'name',
            'brand',
            'brand_name',
            'klass',
            'listings',
            'type',
            'bandwidth',
            'size',
        )
