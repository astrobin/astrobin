# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from django.utils import timezone
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.iotd_archive_serializer import IotdArchiveSerializer
from common.permissions import ReadOnly


class IotdArchiveViewSet(viewsets.ModelViewSet):
    serializer_class = IotdArchiveSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]

    def get_queryset(self) -> QuerySet:
        return self.serializer_class.Meta.model.objects.filter(
            date__lte=timezone.now().date()
        ).select_related(
            'image',
        )
