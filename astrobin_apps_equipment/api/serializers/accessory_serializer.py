from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Accessory


class AccessorySerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Accessory
        fields = '__all__'
        abstract = False


class AccessorySerializerForImage(AccessorySerializer):
    class Meta(AccessorySerializer.Meta):
        fields = (
            'id',
            'name',
            'brand',
            'brand_name',
            'klass',
            'listings',
        )
