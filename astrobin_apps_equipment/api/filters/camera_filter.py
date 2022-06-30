from django.db.models import QuerySet

from astrobin_apps_equipment.api.filters.equipment_item_filter import EquipmentItemFilter
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.services.camera_service import CameraService


class CameraFilter(EquipmentItemFilter):
    def has_pending_review(self, queryset: QuerySet, value, *args, **kwargs):
        queryset = super().has_pending_review(queryset, value, args, kwargs)
        queryset = queryset.filter(CameraService.variant_exclusion_query())

        return queryset

    class Meta(EquipmentItemFilter.Meta):
        model = Camera
        fields = EquipmentItemFilter.Meta.fields + ['modified']
