# -*- coding: utf-8 -*-
from django.http import JsonResponse
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.permissions.is_iotd_judge import IsIotdJudge
from astrobin_apps_iotd.api.queue_pagination import QueuePagination
from astrobin_apps_iotd.api.serializers.judgement_queue_serializer import JudgementQueueSerializer
from astrobin_apps_iotd.services import IotdService
from common.permissions import ReadOnly


class JudgementQueueViewSet(viewsets.ModelViewSet):
    serializer_class = JudgementQueueSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = QueuePagination
    permission_classes = [IsAuthenticated, ReadOnly, IsIotdJudge]
    http_method_names = ['get', 'head']

    def get_queryset(self):
        return IotdService().get_judgement_queue(
            self.request.user,
            self.request.GET.get('sort', None),
        )

    @action(methods=['GET'], detail=False, url_path='cannot-select-now-reason')
    def cannot_select_now_reason(self, request):
        return JsonResponse({'reason': IotdService().judge_cannot_select_now_reason(request.user)})

    @action(methods=['GET'], detail=False, url_path='next-available-selection-time')
    def next_available_selection_time(self, request):
        return JsonResponse(
            {
                'nextAvailableSelectionTime': IotdService().get_next_available_selection_time_for_judge(
                    request.user
                ).isoformat() + 'Z'
            }
        )
