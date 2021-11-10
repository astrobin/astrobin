from astrobin_apps_equipment.api.serializers.equipment_item_edit_proposal_serializer import \
    EquipmentItemEditProposalSerializer
from astrobin_apps_equipment.models import Sensor
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal


class SensorEditProposalSerializer(EquipmentItemEditProposalSerializer):
    def get_original_properties(self, target: Sensor):
        return {
            'quantum_efficiency': target.quantum_efficiency,
            'pixel_size': target.pixel_size,
            'pixel_width': target.pixel_width,
            'pixel_height': target.pixel_height,
            'sensor_width': target.sensor_width,
            'sensor_height': target.sensor_height,
            'full_well_capacity': target.full_well_capacity,
            'read_noise': target.read_noise,
            'frame_rate': target.frame_rate,
            'adc': target.adc,
            'color_or_mono': target.color_or_mono,
            'specification_url': target.specification_url,
        }

    class Meta(EquipmentItemEditProposalSerializer.Meta):
        model = SensorEditProposal
        fields = '__all__'
        abstract = False
