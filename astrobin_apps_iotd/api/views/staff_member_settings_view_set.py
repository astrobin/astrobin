# -*- coding: utf-8 -*-


from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.staff_member_settings_serializer import StaffMemberSettingsSerializer
from astrobin_apps_iotd.models import IotdStaffMemberSettings
from common.permissions import ReadOnly


class StaffMemberSettingsViewSet(viewsets.ModelViewSet):
    serializer_class = StaffMemberSettingsSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated, ReadOnly]
    model = IotdStaffMemberSettings
    http_method_names = ['get', 'head', 'option']

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)
