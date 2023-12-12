from django_filters.rest_framework import DjangoFilterBackend
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_private_conversation_serializer import \
    EquipmentItemMarketplacePrivateConversationSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplacePrivateConversation
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplacePrivateConversationViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('id', 'user')
    queryset = EquipmentItemMarketplacePrivateConversation.objects.all()
    serializer_class = EquipmentItemMarketplacePrivateConversationSerializer
