# -*- coding: utf-8 -*-

from django.http import HttpResponseForbidden
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin.models import Image
from astrobin_apps_iotd.api.permissions.is_iotd_judge import IsIotdJudge
from astrobin_apps_iotd.api.serializers.iotd_serializer import IotdSerializer
from astrobin_apps_iotd.models import Iotd
from astrobin_apps_iotd.permissions import may_elect_iotd, may_unelect_iotd
from common.services import DateTimeService


class FutureIotdsViewSet(viewsets.ModelViewSet):
    serializer_class = IotdSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated, IsIotdJudge]

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(date__gt=DateTimeService.today())

    def create(self, request, *args, **kwargs):
        try:
            image = Image.objects.get(pk=str(request.data.get('image')))
            may, reason = may_elect_iotd(request.user, image)
            if not may:
                return HttpResponseForbidden(reason)
            return super().create(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseForbidden(str(e))

    def destroy(self, request, *args, **kwargs):
        iotd: Iotd = self.get_object()

        may, reason = may_unelect_iotd(request.user, iotd.image)

        if not may:
            return HttpResponseForbidden(reason)

        return super().destroy(request, *args, **kwargs)
