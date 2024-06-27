# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.generics import get_object_or_404
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer, EquipmentItemMarketplacePrivateConversation,
)
from astrobin_apps_equipment.models.equipment_item_marketplace_offer import EquipmentItemMarketplaceOfferStatus
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService
from common.services import DateTimeService
from nested_comments.models import NestedComment


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
        if self.action in ('list', 'retrieve'):
            permission_classes = [
                MayAccessMarketplace
            ]
        elif self.action == 'create':
            permission_classes = [
                permissions.IsAuthenticated,
                MayAccessMarketplace
            ]
        elif self.action in ('update', 'partial_update', 'retract'):
            permission_classes = [
                IsOfferOwner
            ]
        elif self.action in ('accept', 'reject'):
            permission_classes = [
                IsOfferOwnerOrListingOwner
            ]
        else:
            permission_classes = [
                permissions.IsAdminUser
            ]

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

    def create(self, request, *args, **kwargs):
        # Do not allow creating offers for listings that are expired.
        listing = EquipmentItemMarketplaceListing.objects.get(pk=request.data['listing'])
        if listing.expiration < DateTimeService.now():
            raise serializers.ValidationError("Cannot create an offer for an expired listing")

        # Do not allow creating offers if a user already has a pending offer for the same line item.
        line_item = EquipmentItemMarketplaceListingLineItem.objects.get(pk=request.data['line_item'])
        if EquipmentItemMarketplaceOffer.objects.filter(
                line_item=line_item,
                user=request.user,
                status=EquipmentItemMarketplaceOfferStatus.PENDING.value
        ).exists():
            raise serializers.ValidationError("Cannot create an offer for the same line item")

        # Do not allow creating an offer with a different master_offer_uuid if there are already pending offers for
        # other line items in the same listing with a different master_offer_uuid.
        if 'master_offer_uuid' in request.data:
            if EquipmentItemMarketplaceOffer.objects.filter(
                    listing=listing,
                    user=request.user,
                    status=EquipmentItemMarketplaceOfferStatus.PENDING.value
            ).exclude(
                    master_offer_uuid=request.data['master_offer_uuid']
            ).exists():
                raise serializers.ValidationError(
                    "Application error: cannot create an offer with a different master_offer_uuid"
                )

        return super().create(request, *args, **kwargs)

    # Do not allow updating offers that have already been accepted or rejected.
    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.status != EquipmentItemMarketplaceOfferStatus.PENDING.value:
            raise serializers.ValidationError("Cannot edit an offer that has been accepted or rejected")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed("DELETE")

    def perform_create(self, serializer):
        super().perform_create(serializer)

        MarketplaceService.log_event(
            self.request.user,
            'created',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

    def perform_update(self, serializer):
        super().perform_update(serializer)

        MarketplaceService.log_event(
            self.request.user,
            'updated',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

    def perform_destroy(self, instance):
        super().perform_destroy(instance)

        MarketplaceService.log_event(
            self.request.user,
            'deleted',
            self.get_serializer_class(),
            instance,
            context={'request': self.request},
        )

    def create_private_message(self, user, offer, message):
        private_conversation, _ = EquipmentItemMarketplacePrivateConversation.objects.get_or_create(
            user=offer.user,
            listing=offer.listing
        )
        content_type = ContentType.objects.get_for_model(EquipmentItemMarketplacePrivateConversation)
        NestedComment.objects.create(
            content_type=content_type,
            object_id=private_conversation.pk,
            author=user,
            text=message,
        )

        if user == offer.listing.user:
            EquipmentItemMarketplacePrivateConversation.objects.filter(pk=private_conversation.pk).update(
                listing_user_last_accessed=DateTimeService.now(),
            )
        else:
            EquipmentItemMarketplacePrivateConversation.objects.filter(pk=private_conversation.pk).update(
                user_last_accessed=DateTimeService.now(),
            )

    @action(detail=True, methods=['put'], url_path='accept')
    def accept(self, request, *args, **kwargs):
        offer = self.get_object()

        # Only the listing owner can accept an offer
        if offer.line_item.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Do not allow accepting an offer that has already been rejected or retracted
        if offer.status == EquipmentItemMarketplaceOfferStatus.REJECTED.value:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if offer.status == EquipmentItemMarketplaceOfferStatus.RETRACTED.value:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow accepting an offer that has already been accepted
        if offer.status == EquipmentItemMarketplaceOfferStatus.ACCEPTED.value:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow accepting an offer if the line item has already been sold
        if offer.line_item.sold:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow accepting an offer if the line item has already been reserved
        if offer.line_item.reserved:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow accepting an offer if there's another accepted offer for the same line item
        if EquipmentItemMarketplaceOffer.objects.filter(
                line_item=offer.line_item,
                status=EquipmentItemMarketplaceOfferStatus.ACCEPTED.value
        ).exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        MarketplaceService.accept_offer(offer)

        if 'message' in request.data:
            self.create_private_message(request.user, offer, request.data['message'])

        offer.refresh_from_db()
        serializer = self.get_serializer(offer)

        MarketplaceService.log_event(
            self.request.user,
            'accepted',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='reject')
    def reject(self, request, *args, **kwargs):
        offer = self.get_object()

        # Only the listing owner can reject an offer
        if offer.line_item.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Do not allow rejecting an offer that has already been rejected or retracted
        if (
                offer.status == EquipmentItemMarketplaceOfferStatus.REJECTED.value or
                offer.status == EquipmentItemMarketplaceOfferStatus.RETRACTED.value
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow rejecting an offer that has already been accepted if the line item has been sold to the user
        if offer.status == EquipmentItemMarketplaceOfferStatus.ACCEPTED.value and offer.line_item.sold_to == offer.user:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        MarketplaceService.reject_offer(offer)

        if 'message' in request.data:
            self.create_private_message(request.user, offer, request.data['message'])

        offer.refresh_from_db()
        serializer = self.get_serializer(offer)

        MarketplaceService.log_event(
            self.request.user,
            'rejected',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['put'], url_path='retract')
    def retract(self, request, *args, **kwargs):
        offer = self.get_object()

        # Only the offer owner can retract an offer
        if offer.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Do not allow retracting an offer that has already been rejected or retracted
        if (
                offer.status == EquipmentItemMarketplaceOfferStatus.REJECTED.value or
                offer.status == EquipmentItemMarketplaceOfferStatus.RETRACTED.value
        ):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Do not allow retracting an offer that has already been accepted if the line item has been sold to the user
        if offer.status == EquipmentItemMarketplaceOfferStatus.ACCEPTED.value and offer.line_item.sold_to == offer.user:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        MarketplaceService.retract_offer(offer)

        if 'message' in request.data:
            self.create_private_message(request.user, offer, request.data['message'])

        offer.refresh_from_db()
        serializer = self.get_serializer(offer)

        MarketplaceService.log_event(
            self.request.user,
            'retracted',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

        return Response(serializer.data, status=status.HTTP_200_OK)
