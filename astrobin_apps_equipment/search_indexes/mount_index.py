from django.db.models import Q
from haystack.constants import Indexable

from astrobin_apps_equipment.models import Mount
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class MountIndex(EquipmentItemIndex, Indexable):
    def get_model(self):
        return Mount

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Mount) -> Q:
        return Q(mounts_2=obj) | Q(mounts_2__in=obj.variants.all())

    # noinspection PyMethodMayBeStatic
    def user_queryset(self, obj: Mount) -> Q:
        return Q(image__mounts_2=obj) | Q(image__mounts_2__in=obj.variants.all())
