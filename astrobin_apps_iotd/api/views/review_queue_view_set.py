# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.queue_pagination import QueuePagination
from astrobin_apps_iotd.api.serializers.review_queue_serializer import ReviewQueueSerializer
from astrobin_apps_iotd.services import IotdService
from common.permissions import ReadOnly


class ReviewQueueViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewQueueSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = QueuePagination
    permission_classes = [IsAuthenticated, ReadOnly]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return IotdService().get_review_queue(self.request.user)
