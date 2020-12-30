# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.telescope_serializer import TelescopeSerializer
from astrobin.models import Telescope
from common.permissions import ReadOnly


class TelescopeViewSet(viewsets.ModelViewSet):
    serializer_class = TelescopeSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]

    def get_queryset(self):
        return Telescope.objects.all()
