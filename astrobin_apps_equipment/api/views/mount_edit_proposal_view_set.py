from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.mount_edit_proposal_filter import MountEditProposalFilter
from astrobin_apps_equipment.api.serializers.mount_edit_proposal_image_serializer import \
    MountEditProposalImageSerializer
from astrobin_apps_equipment.api.serializers.mount_edit_proposal_serializer import MountEditProposalSerializer
from astrobin_apps_equipment.api.views.equipment_item_edit_proposal_view_set import EquipmentItemEditProposalViewSet
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal


class MountEditProposalViewSet(EquipmentItemEditProposalViewSet):
    serializer_class = MountEditProposalSerializer
    filter_class = MountEditProposalFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=MountEditProposalImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(MountEditProposalViewSet, self).image_upload(request, pk)

    @action(detail=True, methods=['POST'])
    def approve(self, request, pk):
        edit_proposal: MountEditProposal = get_object_or_404(MountEditProposal, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        mount = edit_proposal.edit_proposal_target
        mount.type = edit_proposal.type
        mount.tracking_accuracy = edit_proposal.tracking_accuracy
        mount.pec = edit_proposal.pec
        mount.max_payload = edit_proposal.max_payload
        mount.weight = edit_proposal.computerized
        mount.slew_speed = edit_proposal.slew_speed

        mount.save()

        return super().approve(request, pk)

    class Meta(EquipmentItemEditProposalViewSet.Meta):
        abstract = False
