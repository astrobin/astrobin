from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal


class SoftwareEditProposalImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = SoftwareEditProposal
        abstract = False
