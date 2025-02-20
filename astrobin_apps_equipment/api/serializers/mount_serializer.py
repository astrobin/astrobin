from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Mount


class MountSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Mount
        fields = '__all__'
        abstract = False


class MountSerializerForImage(MountSerializer):
    class Meta(MountSerializer.Meta):
        fields = (
            'id',
            'name',
            'brand',
            'brand_name',
            'klass',
            'listings',
            'type',
            'weight',
            'max_payload',
            'computerized',
            'periodic_error',
            'pec',
            'slew_speed',
        )
