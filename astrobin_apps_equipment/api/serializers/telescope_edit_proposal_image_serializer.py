from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal


class TelescopeEditProposalImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = TelescopeEditProposal
        abstract = True
