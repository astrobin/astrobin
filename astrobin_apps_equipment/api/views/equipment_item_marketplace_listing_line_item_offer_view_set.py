# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService


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
        if self.action in ('list', 'retrieve', 'accept'):
            permission_classes = [MayAccessMarketplace]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated, MayAccessMarketplace]
        elif self.action in ('update', 'partial_update'):
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

    # Do not allow updating offers that have already been accepted or rejected.
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != EquipmentItemMarketplaceOfferStatus.PENDING.value:
            raise serializers.ValidationError("Cannot edit an offer that has been accepted or rejected")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user == instance.line_item.user:
            instance.status = EquipmentItemMarketplaceOfferStatus.REJECTED.value

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='accept')
    def accept(self, request, *args, **kwargs):
        offer = self.get_object()

        if offer.line_item.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        MarketplaceService.accept_offer(offer)

        offer.refresh_from_db()
        serializer = self.get_serializer(offer)
        return Response(serializer.data, status=status.HTTP_200_OK)
