from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal


class AccessoryEditProposalImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = AccessoryEditProposal
        abstract = False
