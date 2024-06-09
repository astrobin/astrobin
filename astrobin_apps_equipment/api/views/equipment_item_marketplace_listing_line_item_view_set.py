from typing import Type

from django.contrib.auth.models import User
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService
from common.constants import GroupName
from common.permissions import IsObjectUser, ReadOnly, is_group_member, or_permission
from common.services import DateTimeService


class EquipmentItemMarketplaceListingLineItemViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [
        or_permission(IsAuthenticated, ReadOnly),
        or_permission(IsObjectUser, is_group_member(GroupName.MARKETPLACE_MODERATORS), ReadOnly),
        MayAccessMarketplace
    ]
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

    def perform_create(self, serializer):
        super().perform_create(serializer)

        MarketplaceService.log_event(
            self.request.user,
            'created',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

    # Do not allow editing a line item that has been sold
    def perform_update(self, serializer):
        instance = serializer.instance

        if instance.sold:
            raise serializers.ValidationError("Cannot edit a line item that has been sold")

        if instance.reserved:
            raise serializers.ValidationError("Cannot edit a line item that has been reserved")

        super().perform_update(serializer)

        MarketplaceService.log_event(
            self.request.user,
            'updated',
            self.get_serializer_class(),
            serializer.instance,
            context={'request': self.request},
        )

    def perform_destroy(self, instance):
        if instance.sold:
            raise serializers.ValidationError("Cannot delete a line item that has been sold")

        super().perform_destroy(instance)

        MarketplaceService.log_event(
            self.request.user,
            'deleted',
            self.get_serializer_class(),
            instance,
            context={'request': self.request},
        )

    @action(detail=True, methods=['put'], url_path='mark-as-sold')
    def mark_as_sold(self, request, pk=None, listing_id=None):
        try:
            line_item = EquipmentItemMarketplaceListingLineItem.objects.get(pk=pk)
        except EquipmentItemMarketplaceListingLineItem.DoesNotExist:
            raise NotFound()

        if line_item.sold:
            raise serializers.ValidationError("This line item has already been marked as sold")

        if line_item.listing.user != request.user:
            raise serializers.ValidationError("You are not the owner of this listing")

        line_item.sold = DateTimeService.now()
        if request.data.get("sold_to"):
            sold_to_id = request.data.get("sold_to")
            if sold_to_id > 0:
                try:
                    line_item.sold_to = User.objects.get(pk=sold_to_id)
                except User.DoesNotExist:
                    raise NotFound()

        line_item.save()

        serializer = self.get_serializer(line_item)

        MarketplaceService.log_event(
            request.user,
            'marked as sold',
            self.get_serializer_class(),
            line_item,
            context={'request': request},
        )

        return Response(serializer.data)
