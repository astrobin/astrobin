# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_remote_source_affiliation.api.filters.remote_source_affiliate_filter import \
    RemoteSourceAffiliateFilter
from astrobin_apps_remote_source_affiliation.api.serializers.remote_source_affiliate_serializer import \
    RemoteSourceAffiliateSerializer
from astrobin_apps_remote_source_affiliation.models import RemoteSourceAffiliate
from common.permissions import ReadOnly


class RemoteSourceAffiliateViewSet(viewsets.ModelViewSet):
    serializer_class = RemoteSourceAffiliateSerializer
    queryset = RemoteSourceAffiliate.objects.all()
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = RemoteSourceAffiliateFilter
    permission_classes = [
        ReadOnly,
    ]
    http_method_names = ['get', 'head']
