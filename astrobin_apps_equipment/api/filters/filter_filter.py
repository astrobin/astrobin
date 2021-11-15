from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Filter


class FilterFilter(EquipmentItemFilter):
    class Meta(EquipmentItemFilter.Meta):
        model = Filter
