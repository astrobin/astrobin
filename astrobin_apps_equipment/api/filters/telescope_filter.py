from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Telescope


class TelescopeFilter(EquipmentItemFilter):
    class Meta(EquipmentItemFilter.Meta):
        model = Telescope
