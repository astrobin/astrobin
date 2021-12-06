from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Accessory


class AccessoryFilter(EquipmentItemFilter):
    class Meta(EquipmentItemFilter.Meta):
        model = Accessory
