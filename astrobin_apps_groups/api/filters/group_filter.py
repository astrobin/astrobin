from django.db import models
from django_filters import IsoDateTimeFilter
from django_filters.rest_framework import FilterSet

from astrobin_apps_groups.models import Group
from common.filters.list_filter import ListFilter


class GroupFilter(FilterSet):
    id = ListFilter(field_name="id", lookup_expr='in')
    members = ListFilter(field_name="members", lookup_expr='in')

    class Meta:
        model = Group
        fields = {
            'id': (),
            'members': (),
            'date_created': ('lt', 'lte', 'exact', 'gt', 'gte'),
            'date_updated': ('lt', 'lte', 'exact', 'gt', 'gte'),
        }

    filter_overrides = {
        models.DateTimeField: {
            'filter_class': IsoDateTimeFilter
        },
    }
