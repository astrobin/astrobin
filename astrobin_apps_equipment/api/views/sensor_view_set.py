from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser

from astrobin_apps_equipment.api.filters.sensor_filter import SensorFilter
from astrobin_apps_equipment.api.serializers.sensor_image_serializer import SensorImageSerializer
from astrobin_apps_equipment.api.serializers.sensor_serializer import SensorSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class SensorViewSet(EquipmentItemViewSet):
    serializer_class = SensorSerializer
    filter_class = SensorFilter

    @action(
        detail=True,
        methods=['POST'],
        serializer_class=SensorImageSerializer,
        parser_classes=[MultiPartParser, FormParser],
    )
    def image(self, request, pk):
        return super(SensorViewSet, self).image_upload(request, pk)
