from django_filters import FilterSet

from astrobin_apps_equipment.models import EquipmentItemGroup


class EquipmentItemGroupFilter(FilterSet):
    class Meta:
        model = EquipmentItemGroup
        fields = '__all__'
