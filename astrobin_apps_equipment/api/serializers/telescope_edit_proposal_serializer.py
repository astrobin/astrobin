from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Telescope
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal


class TelescopeEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Telescope):
        return {
            'type': target.type,
            'aperture': target.aperture,
            'min_focal_length': target.min_focal_length,
            'max_focal_length': target.max_focal_length,
            'weight': target.weight,
        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = TelescopeEditProposal
        fields = '__all__'
        abstract = False
