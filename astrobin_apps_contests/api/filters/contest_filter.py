from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin_apps_contests.models import Contest


class ContestFilter(FilterSet):
    class Meta:
        model = Contest
        fields = {
            'start_date': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'end_date': ('lt', 'lte', 'exact', 'gt', 'gte')
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
