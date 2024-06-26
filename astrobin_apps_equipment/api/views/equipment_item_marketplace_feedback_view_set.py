from datetime import timedelta

from django.db.models import Q
from django.shortcuts import get_object_or_404
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import status, viewsets
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.models import UserProfile
from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_feedback_serializer import \
    EquipmentItemMarketplaceFeedbackSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback,
    EquipmentItemMarketplaceListing,
)
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService
from astrobin_apps_equipment.types.marketplace_feedback_target_type import MarketplaceFeedbackTargetType
from common.permissions import IsObjectUserOrReadOnly
from common.services import DateTimeService


class EquipmentItemMarketplaceFeedbackViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly, MayAccessMarketplace]
    serializer_class = EquipmentItemMarketplaceFeedbackSerializer
    filter_fields = ('user',)

    def get_queryset(self):
        listing_id = self.kwargs.get('listing_id')

        if listing_id is not None:
            listing = get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)

            return EquipmentItemMarketplaceFeedback.objects.filter(
                Q(listing=listing) &
                Q(
                    Q(user=self.request.user) |
                    Q(listing__user=self.request.user)
                )
            )
        else:
            from django.http import Http404
            raise Http404("listing_id not provided")

    def create(self, request, *args, **kwargs):
        listing_id = self.kwargs.get('listing_id')
        recipient = request.data.get('recipient')

        if listing_id is None:
            return Response(
                {"detail": "Listing ID must be provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        if recipient is None:
            return Response(
                {"detail": "Recipient must be provided."}, status=status.HTTP_400_BAD_REQUEST
            )

        listing = get_object_or_404(EquipmentItemMarketplaceListing, pk=listing_id)

        # Determine the target_type based on the user's relationship to the line item
        if request.user == listing.user:
            target_type = MarketplaceFeedbackTargetType.BUYER.value
        else:
            target_type = MarketplaceFeedbackTargetType.SELLER.value

        # Prepare data for update_or_create
        updated_data = request.data.copy()
        updated_data['target_type'] = target_type
        updated_data['user'] = request.user.pk

        # Check for existing feedback
        existing_feedback = EquipmentItemMarketplaceFeedback.objects.filter(
            listing=listing,
            recipient=recipient,
            user=request.user,
        ).first()

        UserProfile.objects.filter(user__pk=recipient).update(
            updated=DateTimeService.now()
        )

        if existing_feedback:
            # Check if feedback is too old to be edited
            max_days = 30
            if existing_feedback.created + timedelta(days=max_days) < DateTimeService.now():
                return Response(
                    {
                        "detail": f"Feedback cannot be edited after {max_days} days."
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update existing feedback
            serializer = self.get_serializer(existing_feedback, data=updated_data)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Create new feedback
            serializer = self.get_serializer(data=updated_data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'PUT' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'PATCH' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method 'DELETE' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
