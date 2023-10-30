from typing import Type

from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingLineItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filterset_fields = ['hash']
    queryset = EquipmentItemMarketplaceListingLineItem.objects.all()

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingLineItemSerializer

        return EquipmentItemMarketplaceListingLineItemReadSerializer
