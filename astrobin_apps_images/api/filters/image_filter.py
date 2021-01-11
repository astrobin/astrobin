from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin.models import Image
from common.filters.list_filter import ListFilter


class ImageFilter(FilterSet):
    ids = ListFilter(name="id", lookup_expr='in')

    class Meta:
        model = Image
        fields = {
            'ids': (),
            'uploaded': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'published': ('lt', 'lte', 'exact', 'gt', 'gte')
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
