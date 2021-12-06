from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.software_filter import SoftwareFilter
from astrobin_apps_equipment.api.serializers.software_image_serializer import SoftwareImageSerializer
from astrobin_apps_equipment.api.serializers.software_serializer import SoftwareSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class SoftwareViewSet(EquipmentItemViewSet):
    serializer_class = SoftwareSerializer
    filter_class = SoftwareFilter

    @action(
        detail=True,
        methods=['post'],
        serializer_class=SoftwareImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(SoftwareViewSet, self).image_upload(request, pk)
