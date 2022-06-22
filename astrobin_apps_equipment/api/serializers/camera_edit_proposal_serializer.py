from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Camera, CameraEditProposal
from astrobin_apps_equipment.models.camera_base_model import CameraType


class CameraEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Camera):
        return {
            'type': target.type,
            'sensor': target.sensor.pk if target.sensor else None,
            'cooled': target.cooled,
            'max_cooling': target.max_cooling,
            'back_focus': target.back_focus,

        }

    def validate(self, attrs):
        target = attrs['edit_proposal_target']
        if target.modified or (target.type == CameraType.DSLR_MIRRORLESS and target.cooled):
            raise ValidationError(
                'Modified and/or cooled DSLR or mirrorless cameras do not support edit proposals. Edit the regular '
                'variant instead.'
            )

        return super().validate(attrs)

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = CameraEditProposal
        fields = '__all__'
        abstract = False
