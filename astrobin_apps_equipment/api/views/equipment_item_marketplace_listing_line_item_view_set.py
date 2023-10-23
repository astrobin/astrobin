from typing import Type

from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingLineItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]

    def get_queryset(self) -> QuerySet:
        return self.get_serializer_class().Meta.model.objects.filter(user=self.request.user)

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingLineItemReadSerializer

        return EquipmentItemMarketplaceListingLineItemSerializer
