from django_filters import FilterSet

from astrobin_apps_equipment.models import Telescope


class TelescopeFilter(FilterSet):
    class Meta:
        model = Telescope
        fields = {
            'name': ["exact"],
        }
