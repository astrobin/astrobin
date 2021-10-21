# -*- coding: utf-8 -*-

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import Gear, Telescope, Camera, FocalReducer, Mount, Accessory, Software, Filter
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly


class GearViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = GearSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_queryset(self):
        return Gear.objects.all()

    @action(methods=['GET'], detail=True, url_path='type')
    def get_type(self, request, pk):
        result = "unknown"

        if Camera.objects.filter(gear_ptr__pk=pk).exists():
            result = "camera"

        elif Telescope.objects.filter(gear_ptr__pk=pk).exists():
            result = "telescope"

        elif FocalReducer.objects.filter(gear_ptr__pk=pk).exists():
            result = "focal-reducer"

        elif Mount.objects.filter(gear_ptr__pk=pk).exists():
            result = "mount"

        elif Filter.objects.filter(gear_ptr__pk=pk).exists():
            result = "filter"

        elif Accessory.objects.filter(gear_ptr__pk=pk).exists():
            result = "accessory"

        elif Software.objects.filter(gear_ptr__pk=pk).exists():
            result = "software"

        return Response(result)
