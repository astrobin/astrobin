from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.telescope_edit_proposal_filter import TelescopeEditProposalFilter
from astrobin_apps_equipment.api.serializers.telescope_edit_proposal_image_serializer import \
    TelescopeEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.telescope_edit_proposal_serializer import TelescopeEditProposalSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.telescope_edit_proposal import TelescopeEditProposal


class TelescopeEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = TelescopeEditProposalSerializer
    filter_class = TelescopeEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=TelescopeEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(TelescopeEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: TelescopeEditProposal = get_object_or_404(TelescopeEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        telescope = edit_proposal.edit_proposal_target
        telescope.type = edit_proposal.type
        telescope.aperture = edit_proposal.aperture
        telescope.min_focal_length = edit_proposal.min_focal_length
        telescope.max_focal_length = edit_proposal.max_focal_length
        telescope.weight = edit_proposal.weight

        telescope.save()

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
