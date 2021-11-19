from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin.models import ImageRevision
from common.filters.list_filter import ListFilter


class ImageRevisionFilter(FilterSet):
    image = ListFilter(field_name="image__pk", lookup_expr='in')

    class Meta:
        model = ImageRevision
        fields = {
            'uploaded': ('lt', 'lte', 'exact', 'gt', 'gte'),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
