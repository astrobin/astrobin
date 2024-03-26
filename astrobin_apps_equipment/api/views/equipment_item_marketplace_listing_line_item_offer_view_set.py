# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from common.permissions import IsObjectUserOrReadOnly


class IsOfferOwner(permissions.BasePermission):
    """
    Custom permission to allow only the offer owner to modify the offer.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsOfferOwnerOrListingOwner(permissions.BasePermission):
    """
    Custom permission to allow the offer owner or the listing owner to delete the offer.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or obj.listing.user == request.user


class EquipmentItemMarketplaceOfferViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    serializer_class = EquipmentItemMarketplaceOfferSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [IsOfferOwner]
        elif self.action == 'destroy':
            permission_classes = [IsOfferOwnerOrListingOwner]
        else:
            permission_classes = [permissions.IsAdminUser]

        return [permission() for permission in permission_classes]

    def get_queryset(self) -> QuerySet:
        listing_id = self.kwargs.get('listing_id')
        line_item_id = self.kwargs.get('line_item_id')

        if listing_id is not None or line_item_id is not None:
            # Check if the listing exists and raise 404 if not
            listing = get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)
            get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)

            if self.request.user == listing.user:
                return EquipmentItemMarketplaceOffer.objects.filter(listing_id=listing_id)

            if self.request.user.is_authenticated:
                return EquipmentItemMarketplaceOffer.objects.filter(
                    listing_id=listing_id, user=self.request.user
                )

            return EquipmentItemMarketplaceOffer.objects.none()
        else:
            # Raise a 404 error if listing_id is not provided in the URL
            from django.http import Http404
            raise Http404("Listing ID or LineItem ID not provided")
