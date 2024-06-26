from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.permissions.may_access_marketplace import MayAccessMarketplace
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_feedback_serializer import \
    EquipmentItemMarketplaceFeedbackSerializer
from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceFeedback,
)
from common.permissions import ReadOnly


class EquipmentItemMarketplaceUserFeedbackViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [MayAccessMarketplace, ReadOnly]
    serializer_class = EquipmentItemMarketplaceFeedbackSerializer

    def get_queryset(self):
        user_id = self.kwargs.get('user_id')

        if user_id is not None:
            user = get_object_or_404(User, pk=user_id)
            return EquipmentItemMarketplaceFeedback.objects.filter(recipient=user)
        else:
            from django.http import Http404
            raise Http404("user_id not provided")
