# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.api2.serializers.gear_user_info_serializer import GearUserInfoSerializer
from astrobin.api2.views.migratable_item_mixin import MigratableItemMixin
from astrobin.models import GearUserInfo
from common.permissions import ReadOnly


class GearUserInfoViewSet(MigratableItemMixin, viewsets.ModelViewSet):
    serializer_class = GearUserInfoSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    filter_fields = ('gear', 'user')
    http_method_names = ('get', 'head')

    def get_queryset(self):
        return GearUserInfo.objects.all()
