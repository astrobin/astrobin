from django.db.models import Q
from haystack.constants import Indexable

from astrobin_apps_equipment.models import Software
from astrobin_apps_equipment.search_indexes.equipment_item_index import EquipmentItemIndex


class SoftwareIndex(EquipmentItemIndex, Indexable):
    def get_model(self):
        return Software

    # noinspection PyMethodMayBeStatic
    def image_queryset(self, obj: Software) -> Q:
        return Q(software_2=obj) | Q(software_2__in=obj.variants.all())

    # noinspection PyMethodMayBeStatic
    def user_queryset(self, obj: Software) -> Q:
        return Q(image__software_2=obj) | Q(image__software_2__in=obj.variants.all())
