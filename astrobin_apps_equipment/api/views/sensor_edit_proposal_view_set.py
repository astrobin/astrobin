from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.sensor_edit_proposal_filter import SensorEditProposalFilter
from astrobin_apps_equipment.api.serializers.sensor_edit_proposal_image_serializer import \
    SensorEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.sensor_edit_proposal_serializer import SensorEditProposalSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.sensor_edit_proposal import SensorEditProposal


class SensorEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = SensorEditProposalSerializer
    filter_class = SensorEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=SensorEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(SensorEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: SensorEditProposal = get_object_or_404(SensorEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        sensor = edit_proposal.edit_proposal_target
        sensor.quantum_efficiency = edit_proposal.quantum_efficiency
        sensor.pixel_size = edit_proposal.pixel_size
        sensor.pixel_width = edit_proposal.pixel_width
        sensor.pixel_height = edit_proposal.pixel_height
        sensor.sensor_width = edit_proposal.sensor_width
        sensor.sensor_height = edit_proposal.sensor_height
        sensor.full_well_capacity = edit_proposal.full_well_capacity
        sensor.read_noise = edit_proposal.read_noise
        sensor.frame_rate = edit_proposal.frame_rate
        sensor.adc = edit_proposal.adc
        sensor.color_or_mono = edit_proposal.color_or_mono

        sensor.save()

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
