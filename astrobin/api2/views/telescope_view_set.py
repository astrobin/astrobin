# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.telescope_serializer import TelescopeSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import Telescope
from common.permissions import ReadOnly


class TelescopeViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = TelescopeSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return Telescope.objects.all()
