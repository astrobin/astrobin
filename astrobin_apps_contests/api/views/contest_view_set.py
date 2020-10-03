# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_contests.api.filters import ContestFilter
from astrobin_apps_contests.api.serializers import ContestSerializer
from astrobin_apps_contests.models import Contest
from common.permissions import IsAdminUserOrReadOnly


class ContestViewSet(viewsets.ModelViewSet):
    serializer_class = ContestSerializer
    queryset = Contest.objects.all()
    permission_classes = [IsAdminUserOrReadOnly]
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    filter_class = ContestFilter
