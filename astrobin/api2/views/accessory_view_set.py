# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.accessory_serializer import AccessorySerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import Accessory
from common.permissions import ReadOnly


class AccessoryViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = AccessorySerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return Accessory.objects.all()
