from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Mount
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal


class MountEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Mount):
        return {
            'type': target.type,
            'tracking_accuracy': target.tracking_accuracy,
            'pec': target.pec,
            'weight': target.weight,
            'max_payload': target.max_payload,
            'computerized': target.computerized,
            'slew_speed': target.slew_speed,
        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = MountEditProposal
        fields = '__all__'
        abstract = False
