from django.db import models
from django_filters import FilterSet, IsoDateTimeFilter

from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate


class RemoteSourceAffiliateFilter(FilterSet):
    class Meta:
        model = RemoteSourceAffiliate
        fields = {
            'code': ('exact',),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
