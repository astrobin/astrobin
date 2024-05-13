from django.db.models import Q
from django.shortcuts import get_object_or_404
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_feedback_serializer import \
    EquipmentItemMarketplaceFeedbackSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback,
    EquipmentItemMarketplaceListingLineItem,
)
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceFeedbackViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    serializer_class = EquipmentItemMarketplaceFeedbackSerializer
    filter_fields = ('user',)

    def get_queryset(self):
        line_item_id = self.kwargs.get('line_item_id')

        if line_item_id is not None:
            line_item = get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)

            return EquipmentItemMarketplaceFeedback.objects.filter(
                Q(line_item=line_item) &
                Q(
                    Q(user=self.request.user) |
                    Q(line_item__listing__user=self.request.user)
                )
            )
        else:
            from django.http import Http404
            raise Http404("line_item_id not provided")
