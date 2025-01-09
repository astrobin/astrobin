# -*- coding: utf-8 -*-
from django.db.models import QuerySet
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.top_pick_archive_serializer import TopPickArchiveSerializer
from common.permissions import ReadOnly


class TopPickArchiveViewSet(viewsets.ModelViewSet):
    serializer_class = TopPickArchiveSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    permission_classes = [ReadOnly]

    def get_queryset(self) -> QuerySet:
        return self.serializer_class.Meta.model.objects.all().select_related(
            'image',
        )
