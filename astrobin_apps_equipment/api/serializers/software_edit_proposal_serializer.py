from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal

from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Software


class SoftwareEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Software):
        return {}

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = SoftwareEditProposal
        fields = '__all__'
        abstract = False
