# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.focal_reducer_serializer import FocalReducerSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import FocalReducer
from common.permissions import ReadOnly


class FocalReducerViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = FocalReducerSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return FocalReducer.objects.all()
