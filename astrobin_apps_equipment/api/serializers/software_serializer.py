from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Software


class SoftwareSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Software
        fields = '__all__'
        abstract = False


class SoftwareSerializerForImage(SoftwareSerializer):
    class Meta(SoftwareSerializer.Meta):
        fields = (
            'id',
            'name',
            'brand',
            'brand_name',
            'klass',
            'listings',
        )
