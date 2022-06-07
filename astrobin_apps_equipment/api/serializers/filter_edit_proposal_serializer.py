from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Filter
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal


class FilterEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Filter):
        return {
            'type': target.type,
            'bandwidth': target.bandwidth,
        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = FilterEditProposal
        fields = '__all__'
        abstract = False
