# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.gear_serializer import GearSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import Gear
from astrobin_apps_equipment.api.permissions.is_equipment_moderator_or_read_only import IsEquipmentModeratorOrReadOnly


class GearViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = GearSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [IsEquipmentModeratorOrReadOnly]
    http_method_names = ['get', 'post', 'head', 'put', 'patch']

    def get_queryset(self):
        return Gear.objects.all()
