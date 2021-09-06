from django_filters import FilterSet

from astrobin_apps_equipment.models import Camera


class CameraFilter(FilterSet):
    class Meta:
        model = Camera
        fields = {
            'name': ["exact"],
        }
