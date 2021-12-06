from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal


class MountEditProposalImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = MountEditProposal
        abstract = False
