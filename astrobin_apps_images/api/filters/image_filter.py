from django.contrib.postgres.search import TrigramDistance
from django.db import models
from django.db.models import Q, QuerySet
from django_filters import CharFilter, FilterSet, IsoDateTimeFilter

from astrobin.models import Image


class ImageFilter(FilterSet):
    q = CharFilter(method='search')

    def search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.annotate(
            distance=TrigramDistance('title', value)
        ).filter(
            Q(distance__lte=0.5) |
            Q(title__icontains=value)
        ).order_by('distance')

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
