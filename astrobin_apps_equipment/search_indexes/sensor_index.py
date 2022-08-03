from django.db.models import Q
from haystack.constants import Indexable

from astrobin_apps_equipment.models import Sensor
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class SensorIndex(EquipmentItemIndex, Indexable):
    def get_model(self):
        return Sensor

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Sensor) -> Q:
        return Q(imaging_cameras_2__sensor=obj) | \
               Q(guiding_cameras_2__sensor=obj) | \
               Q(imaging_cameras_2__sensor__in=obj.variants.all()) | \
               Q(guiding_cameras_2__sensor__in=obj.variants.all())

    # noinspection PyMethodMayBeStatic
    def user_queryset(self, obj: Sensor) -> Q:
        return Q(image__imaging_cameras_2__sensor=obj) | \
               Q(image__guiding_cameras_2__sensor=obj) | \
               Q(image__imaging_cameras_2__sensor__in=obj.variants.all()) | \
               Q(image__guiding_cameras_2__sensor__in=obj.variants.all())
