from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin_apps_payments.models import ExchangeRate


class ExchangeRateFilter(FilterSet):
    class Meta:
        model = ExchangeRate
        fields = {
            'source': ('exact',),
            'target': ('exact',),
            'time': ('lt', 'lte', 'exact', 'gt', 'gte')
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
