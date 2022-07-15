from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.accessory_edit_proposal_filter import AccessoryEditProposalFilter
from astrobin_apps_equipment.api.serializers.accessory_edit_proposal_image_serializer import \
    AccessoryEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.accessory_edit_proposal_serializer import AccessoryEditProposalSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.accessory_edit_proposal import AccessoryEditProposal


class AccessoryEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = AccessoryEditProposalSerializer
    filter_class = AccessoryEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=AccessoryEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(AccessoryEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: AccessoryEditProposal = get_object_or_404(AccessoryEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        accessory = edit_proposal.edit_proposal_target
        accessory.type = edit_proposal.type

        accessory.save()

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
