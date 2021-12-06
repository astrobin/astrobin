from django_filters import FilterSet

from astrobin_apps_equipment.models import EquipmentBrand


class EquipmentBrandFilter(FilterSet):
    class Meta:
        model = EquipmentBrand
        fields = {
            'name': ["exact"],
            'website': ["exact"],
        }
