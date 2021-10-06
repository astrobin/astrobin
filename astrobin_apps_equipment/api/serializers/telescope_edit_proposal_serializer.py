from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal


class TelescopeEditProposalSerializer(EquipmentItemEditProposalSerializer):
    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = TelescopeEditProposal
        fields = '__all__'
        abstract = False
