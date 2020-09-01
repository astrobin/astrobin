# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db.models import QuerySet
from django.http import QueryDict
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_images.api.filters import ThumbnailGroupFilter
from astrobin_apps_images.api.serializers import ThumbnailGroupSerializer
from astrobin_apps_images.models import ThumbnailGroup
from common.permissions import ReadOnly


class ThumbnailGroupViewSet(viewsets.ModelViewSet):
    serializer_class = ThumbnailGroupSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    parser_classes = [CamelCaseJSONParser]
    permission_classes = [ReadOnly]
    filter_classes = [ThumbnailGroupFilter]

    def get_queryset(self):
        objects =  ThumbnailGroup.objects.all()  # type: QuerySet
        q = self.request.query_params  # type: QueryDict

        if 'image' in q:
            objects = objects.filter(image__pk = q['image'])

        return objects
