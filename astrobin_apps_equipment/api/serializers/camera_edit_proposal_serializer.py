from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import CameraEditProposal, Camera


class CameraEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Camera):
        return {
            'type': target.type,
            'sensor': target.sensor.pk if target.sensor else None,
            'cooled': target.cooled,
            'max_cooling': target.max_cooling,
            'back_focus': target.back_focus,

        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = CameraEditProposal
        fields = '__all__'
        abstract = False