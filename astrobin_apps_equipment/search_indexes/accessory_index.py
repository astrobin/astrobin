from django.db.models import Q
from haystack.constants import Indexable

from astrobin_apps_equipment.models import Accessory
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class AccessoryIndex(EquipmentItemIndex, Indexable):
    def get_model(self):
        return Accessory

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Accessory) -> Q:
        return Q(accessories_2=obj) | Q(accessories_2__in=obj.variants.all())
