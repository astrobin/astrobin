from django.contrib.postgres.search import SearchVector
from django.db import models
from django.db.models import QuerySet
from django_filters import CharFilter, FilterSet, IsoDateTimeFilter

from astrobin.models import Image
from common.filters.list_filter import ListFilter


class ImageFilter(FilterSet):
    id = ListFilter(field_name="id", lookup_expr='in')
    hash = ListFilter(field_name="hash", lookup_expr='in')
    q = CharFilter(method='search')
    collection = ListFilter(field_name="collections", lookup_expr='in')

    def search(self, queryset: QuerySet, name, value):
        return queryset.annotate(search=SearchVector('title', 'description')).filter(search=value)

    class Meta:
        model = Image
        fields = {
            'id': (),
            'hash': (),
            'user': ('exact',),
            'uploaded': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'published': ('lt', 'lte', 'exact', 'gt', 'gte'),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
