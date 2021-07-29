from astrobin_apps_equipment.api.serializers.sensor_serializer import SensorSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class SensorViewSet(EquipmentItemViewSet):
    serializer_class = SensorSerializer
