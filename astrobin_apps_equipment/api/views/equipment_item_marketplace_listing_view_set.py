from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.api.serializers.equipment_preset_serializer import EquipmentPresetSerializer
from common.permissions import IsObjectUserOrReadOnly


class EquipmentItemMarketplaceListingViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [IsObjectUserOrReadOnly]
    serializer_class = EquipmentItemMarketplaceListingSerializer

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(user=self.request.user)
