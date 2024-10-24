from django.contrib.postgres.search import SearchVector
from django.db import models
from django.db.models import QuerySet
from django_filters import CharFilter, FilterSet, IsoDateTimeFilter

from astrobin.models import Image


class ImageFilter(FilterSet):
    q = CharFilter(method='search')

    def search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.annotate(
            search=SearchVector('title', 'description')
        ).filter(search__icontains=value)

    class Meta:
        model = Image
        fields = {
            'uploaded': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'published': ('lt', 'lte', 'exact', 'gt', 'gte'),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
