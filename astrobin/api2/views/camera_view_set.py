# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.api2.serializers.camera_serializer import CameraSerializer
from astrobin.models import Camera
from common.permissions import ReadOnly


class CameraViewSet(viewsets.ModelViewSet):
    serializer_class = CameraSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return Camera.objects.all()

    @list_route(url_path='random-non-migrated')
    def random_non_migrated(self, request):
        queryset = self.get_queryset().filter(migration_flag__isnull=True).order_by('?')[:1]
        serializer = CameraSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
