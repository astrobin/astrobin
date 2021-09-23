from django_filters import rest_framework as filters

from astrobin_apps_platesolving.models import PlateSolvingAdvancedTask


class AdvancedTaskFilter(filters.FilterSet):
    class Meta:
        model = PlateSolvingAdvancedTask
        fields = [
            'active',
        ]
