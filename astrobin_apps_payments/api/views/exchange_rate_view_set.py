# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_payments.api.filters.exchange_rate_filter import ExchangeRateFilter
from astrobin_apps_payments.api.serializers.exchange_rate_serializer import ExchangeRateSerializer
from astrobin_apps_payments.models import ExchangeRate
from common.permissions import ReadOnly


class ExchangeRateViewSet(viewsets.ModelViewSet):
    serializer_class = ExchangeRateSerializer
    queryset = ExchangeRate.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ExchangeRateFilter
    pagination_class = LimitOffsetPagination
    permission_classes = [
        ReadOnly,
    ]
    http_method_names = ['get', 'head']
