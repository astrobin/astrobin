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
    EquipmentItemMarketplaceListingLineItem,
)
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
        line_item_id = self.kwargs.get('line_item_id')

        if line_item_id is not None:
            line_item = get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)

            return EquipmentItemMarketplaceFeedback.objects.filter(
                Q(line_item=line_item) &
                Q(
                    Q(user=self.request.user) |
                    Q(line_item__listing__user=self.request.user)
                )
            )
        else:
            from django.http import Http404
            raise Http404("line_item_id not provided")

    def create(self, request, *args, **kwargs):
        line_item_id = self.kwargs.get('line_item_id')
        category = request.data.get('category')

        if line_item_id is not None and category is not None:
            line_item = get_object_or_404(EquipmentItemMarketplaceListingLineItem, pk=line_item_id)
            existing_feedback = EquipmentItemMarketplaceFeedback.objects.filter(
                line_item=line_item,
                user=request.user,
                category=category
            ).exists()

            if existing_feedback:
                return Response(
                    {"detail": "Feedback by this user for this line item and category already exists."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if request.user == line_item.listing.user:
                target_type = MarketplaceFeedbackTargetType.BUYER.value
            else:
                target_type = MarketplaceFeedbackTargetType.SELLER.value

            request.data['target_type'] = target_type

            retval = super().create(request, *args, **kwargs)

            UserProfile.objects.filter(user=request.user).update(
                updated=DateTimeService.now()
            )

            return retval
        else:
            return Response(
                {"detail": "Line item ID and category must be provided."}, status=status.HTTP_400_BAD_REQUEST
            )

    def update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'PUT' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, *args, **kwargs):
        return Response({"detail": "Method 'PATCH' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, *args, **kwargs):
        return Response({"detail": "Method 'DELETE' not allowed."}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
