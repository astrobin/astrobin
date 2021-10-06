from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.telescope_filter import TelescopeFilter
from astrobin_apps_equipment.api.serializers.telescope_image_serializer import TelescopeImageSerializer
from astrobin_apps_equipment.api.serializers.telescope_serializer import TelescopeSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class TelescopeViewSet(EquipmentItemViewSet):
    serializer_class = TelescopeSerializer
    filter_class = TelescopeFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=TelescopeImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(TelescopeViewSet, self).image_upload(request, pk)
