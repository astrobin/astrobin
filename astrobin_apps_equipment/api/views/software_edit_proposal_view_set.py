from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.software_edit_proposal_filter import SoftwareEditProposalFilter
from astrobin_apps_equipment.api.serializers.software_edit_proposal_image_serializer import \
    SoftwareEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.software_edit_proposal_serializer import SoftwareEditProposalSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.software_edit_proposal import SoftwareEditProposal


class SoftwareEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = SoftwareEditProposalSerializer
    filter_class = SoftwareEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=SoftwareEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(SoftwareEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: SoftwareEditProposal = get_object_or_404(SoftwareEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
