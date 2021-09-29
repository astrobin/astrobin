from __future__ import annotations

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from rest_framework.status import HTTP_400_BAD_REQUEST

from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin


class EquipmentItemEditProposalViewSet(EquipmentItemViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def check_edit_proposal_permissions(self, request, edit_proposal):
        if edit_proposal.edit_proposal_reviewed_by is not None:
            return False, Response('This edit proposal was already reviewed', HTTP_400_BAD_REQUEST)

        if edit_proposal.edit_proposal_by == request.user:
            return False, Response('You cannot review nd edit proposal that you proposed', HTTP_400_BAD_REQUEST)

        return True, None

    def approve(self, request, pk):
        edit_proposal: (EquipmentItemEditProposalMixin | EquipmentItem) = get_object_or_404(
            self.get_serializer().Meta.model, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        edit_proposal.edit_proposal_reviewed_by = request.user
        edit_proposal.edit_proposal_review_ip = request.META.get('REMOTE_ADDR')
        edit_proposal.edit_proposal_review_timestamp = timezone.now()
        edit_proposal.edit_proposal_review_comment = request.data.get('comment')
        edit_proposal.edit_proposal_review_status = 'APPROVED'

        target = edit_proposal.edit_proposal_target
        target.name = edit_proposal.name
        target.image = edit_proposal.image

        target.save()
        edit_proposal.save()

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    @action(detail=True, methods=['POST'])
    def reject(self, request, pk):
        edit_proposal: EquipmentItemEditProposalMixin = get_object_or_404(self.get_serializer().Meta.model, pk=pk)

        check_permissions, response = self.check_edit_proposal_permissions(request, edit_proposal)
        if not check_permissions:
            return response

        edit_proposal.edit_proposal_reviewed_by = request.user
        edit_proposal.edit_proposal_review_ip = request.META.get('REMOTE_ADDR')
        edit_proposal.edit_proposal_review_timestamp = timezone.now()
        edit_proposal.edit_proposal_review_comment = request.data.get('comment')
        edit_proposal.edit_proposal_review_status = 'REJECTED'

        edit_proposal.save()

        serializer = self.serializer_class(edit_proposal)
        return Response(serializer.data)

    class Meta(EquipmentItemViewSet.Meta):
        abstract = True
