from typing import Type

from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingLineItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filterset_fields = ['hash']

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_id')
        if listing_id is not None:
            # Check if the listing exists and raise 404 if not
            get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)
            return EquipmentItemMarketplaceListingLineItem.objects.filter(listing_id=listing_id)
        else:
            # Raise a 404 error if listing_id is not provided in the URL
            from django.http import Http404
            raise Http404("Listing ID not provided")

    def get_serializer_class(self) -> Type[serializers.ModelSerializer]:
        if self.request.method in ['PUT', 'POST']:
            return EquipmentItemMarketplaceListingLineItemSerializer

        return EquipmentItemMarketplaceListingLineItemReadSerializer
