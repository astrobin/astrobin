from django_filters import FilterSet

from astrobin_apps_equipment.models import Sensor


class SensorFilter(FilterSet):
    class Meta:
        model = Sensor
        fields = {
            'name': ["exact"],
        }
