from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal

from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Accessory


class AccessoryEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Accessory):
        return {
            'type': target.type,
        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = AccessoryEditProposal
        fields = '__all__'
        abstract = False
