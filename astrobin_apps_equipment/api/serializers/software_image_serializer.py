from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models import Software


class SoftwareImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = Software
        abstract = False
