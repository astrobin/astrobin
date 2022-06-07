from astrobin_apps_equipment.api.serializers.filter_edit_proposal_image_serializer import \
    FilterEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.filter_edit_proposal_serializer import FilterEditProposalSerializer
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.filter_edit_proposal_filter import FilterEditProposalFilter
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal


class FilterEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = FilterEditProposalSerializer
    filter_class = FilterEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=FilterEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(FilterEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: FilterEditProposal = get_object_or_404(FilterEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        filter = edit_proposal.edit_proposal_target
        filter.type = edit_proposal.type
        filter.bandwidth = edit_proposal.bandwidth

        filter.save()

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
