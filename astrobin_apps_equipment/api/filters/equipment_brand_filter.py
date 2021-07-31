from django.db import models
from django_filters import FilterSet, CharFilter

from astrobin_apps_equipment.models import EquipmentBrand


class EquipmentBrandFilter(FilterSet):
    class Meta:
        model = EquipmentBrand
        fields = {
            'name': ["exact"],
        }
        filter_overrides = {
            models.CharField: {
                'filter_class': CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }
