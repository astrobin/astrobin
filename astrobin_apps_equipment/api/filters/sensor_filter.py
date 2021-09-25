from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Sensor


class SensorFilter(EquipmentItemFilter):
    class Meta(EquipmentItemFilter.Meta):
        model = Sensor
