from django.db.models import Q

from astrobin_apps_equipment.models import Filter
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class FilterIndex(EquipmentItemIndex):
    def get_model(self):
        return Filter

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Filter) -> Q:
        return Q(filters_2=obj)
