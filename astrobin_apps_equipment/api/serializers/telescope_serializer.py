from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Telescope


class TelescopeSerializer(EquipmentItemSerializer):
    class Meta(EquipmentItemSerializer.Meta):
        model = Telescope
        fields = '__all__'
        abstract = False


class TelescopeSerializerForImage(TelescopeSerializer):
    class Meta(TelescopeSerializer.Meta):
        fields = (
            'id',
            'name',
            'brand',
            'brand_name',
            'klass',
            'listings',
            'type',
            'aperture',
            'min_focal_length',
            'max_focal_length',
            'weight',
        )
