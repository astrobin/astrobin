from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin.models import Image


class ImageFilter(FilterSet):
    class Meta:
        model = Image
        fields = {
            'uploaded': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'published': ('lt', 'lte', 'exact', 'gt', 'gte')
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
