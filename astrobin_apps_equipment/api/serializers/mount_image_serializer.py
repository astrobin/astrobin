from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models import Mount


class MountImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = Mount
        abstract = False
