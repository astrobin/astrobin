from astrobin_apps_equipment.api.filters.telescope_filter import TelescopeFilter
from astrobin_apps_equipment.api.serializers.telescope_serializer import TelescopeSerializer
from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class TelescopeViewSet(EquipmentItemViewSet):
    serializer_class = TelescopeSerializer
    filter_class = TelescopeFilter
