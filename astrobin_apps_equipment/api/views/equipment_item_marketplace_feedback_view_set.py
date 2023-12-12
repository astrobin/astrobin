from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_feedback_serializer import \
    EquipmentItemMarketplaceFeedbackSerializer
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceFeedbackViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    serializer_class = EquipmentItemMarketplaceFeedbackSerializer
    filter_fields = ('user',)

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(user=self.request.user)
