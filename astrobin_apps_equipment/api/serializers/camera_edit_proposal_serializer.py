from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import CameraEditProposal


class CameraEditProposalSerializer(EquipmentItemEditProposalSerializer):
    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = CameraEditProposal
        fields = '__all__'
        abstract = False
