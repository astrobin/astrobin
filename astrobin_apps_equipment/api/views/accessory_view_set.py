from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.accessory_filter import AccessoryFilter
from astrobin_apps_equipment.api.serializers.accessory_image_serializer import AccessoryImageSerializer
from astrobin_apps_equipment.api.serializers.accessory_serializer import AccessorySerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class AccessoryViewSet(EquipmentItemViewSet):
    serializer_class = AccessorySerializer
    filter_class = AccessoryFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=AccessoryImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(AccessoryViewSet, self).image_upload(request, pk)
