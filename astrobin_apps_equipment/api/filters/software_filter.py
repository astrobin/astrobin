from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Software


class SoftwareFilter(EquipmentItemFilter):
    class Meta(EquipmentItemFilter.Meta):
        model = Software
