# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceListingLineItemImage, EquipmentItemMarketplaceOffer,
)
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceOfferViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        IsObjectUserOrReadOnly
    ]
    serializer_class = EquipmentItemMarketplaceOfferSerializer

    def get_queryset(self) -> QuerySet:
        listing_id = self.kwargs.get('listing_id')
        line_item_id = self.kwargs.get('line_item_id')

        if listing_id is not None or line_item_id is not None:
            # Check if the listing exists and raise 404 if not
            get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)
            get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)
            return EquipmentItemMarketplaceOffer.objects.filter(
                listing_id=listing_id,
            )
        else:
            # Raise a 404 error if listing_id is not provided in the URL
            from django.http import Http404
            raise Http404("Listing ID or LineItem ID not provided")
