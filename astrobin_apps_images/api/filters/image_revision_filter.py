from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin.models import Image, ImageRevision


class ImageRevisionFilter(FilterSet):
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
