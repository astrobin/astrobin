from django.db.models import Q

from astrobin_apps_equipment.models import Sensor
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class SensorIndex(EquipmentItemIndex):
    def get_model(self):
        return Sensor

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Sensor) -> Q:
        return Q(imaging_cameras_2__sensor=obj) | Q(guiding_cameras_2__sensor=obj)
