# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceListingLineItemImage,
)
from common.constants import GroupName
from common.permissions import IsObjectUser, ReadOnly, is_group_member, or_permission


class EquipmentItemMarketplaceListingLineItemImageViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [
        or_permission(IsAuthenticated, ReadOnly),
        or_permission(IsObjectUser, is_group_member(GroupName.MARKETPLACE_MODERATORS), ReadOnly),
    ]
    serializer_class = EquipmentItemMarketplaceListingLineItemImageSerializer
    filterset_fields = ['hash']

    def get_queryset(self) -> QuerySet:
        listing_id = self.kwargs.get('listing_id')
        line_item_id = self.kwargs.get('line_item_id')

        if listing_id is not None or line_item_id is not None:
            # Check if the listing exists and raise 404 if not
            get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)
            get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)
            return EquipmentItemMarketplaceListingLineItemImage.objects.filter(
                line_item_id=line_item_id,
                line_item__listing_id=listing_id,
            )
        else:
            # Raise a 404 error if listing_id is not provided in the URL
            from django.http import Http404
            raise Http404("Listing ID or LineItem ID not provided")
