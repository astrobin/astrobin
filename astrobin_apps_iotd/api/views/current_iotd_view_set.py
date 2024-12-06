# -*- coding: utf-8 -*-

from django.utils import timezone
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.iotd_serializer import IotdSerializer
from common.permissions import ReadOnly


class CurrentIotdViewSet(viewsets.ModelViewSet):
    serializer_class = IotdSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [ReadOnly]

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.filter(
            date__lte=timezone.now().date()
        ).order_by(
            '-date'
        ).select_related(
            'image',
            'image__user',
            'image__user__userprofile'
        )[:1]
