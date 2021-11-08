# -*- coding: utf-8 -*-
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from astrobin.api2.serializers.camera_rename_proposal_serializer import CameraRenameProposalSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import CameraRenameProposal
from common.permissions import IsObjectUserOrReadOnly


class CameraRenameProposalViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = CameraRenameProposalSerializer
    filter_fields = ['status',]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser,]
    permission_classes = [IsObjectUserOrReadOnly]
    http_method_names = ['get', 'head', 'put']
    pagination_class = None

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return CameraRenameProposal.objects.none()

        return CameraRenameProposal.objects.filter(user=self.request.user)

    @action(detail=True, methods=['put'])
    def approve(self, request, pk):
        proposal = get_object_or_404(CameraRenameProposal, pk=pk)

        if request.user != proposal.user:
            return Response(status=HTTP_403_FORBIDDEN)

        if proposal.status != 'PENDING':
            return Response(status=HTTP_400_BAD_REQUEST)

        proposal.status = 'APPROVED'
        proposal.save()

        return Response(self.serializer_class(proposal).data)


    @action(detail=True, methods=['put'])
    def reject(self, request, pk):
        proposal = get_object_or_404(CameraRenameProposal, pk=pk)

        if request.user != proposal.user:
            return Response(status=HTTP_403_FORBIDDEN)

        if proposal.status != 'PENDING':
            return Response(status=HTTP_400_BAD_REQUEST)

        proposal.status = 'REJECTED'
        proposal.reject_reason = request.data.get('reject_reason')
        proposal.save()

        return Response(self.serializer_class(proposal).data)
