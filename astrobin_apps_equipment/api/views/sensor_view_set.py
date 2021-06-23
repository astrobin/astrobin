from astrobin_apps_equipment.api.serializers.sensor_serializer import SensorSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet
from astrobin_apps_equipment.models import Sensor


class SensorViewSet(EquipmentItemViewSet):
    serializer_class = SensorSerializer
    queryset = Sensor.objects.all()
