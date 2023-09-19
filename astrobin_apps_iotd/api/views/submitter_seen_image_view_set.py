# -*- coding: utf-8 -*-


from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.submitter_seen_image_serializer import SubmitterSeenImageSerializer
from astrobin_apps_iotd.models import IotdSubmitterSeenImage


class SubmitterSeenImageViewSet(viewsets.ModelViewSet):
    serializer_class = SubmitterSeenImageSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated]
    model = IotdSubmitterSeenImage
    http_method_names = ['get', 'head', 'options', 'post']

    def get_queryset(self):
        max_days = \
            settings.IOTD_SUBMISSION_WINDOW_DAYS + \
            settings.IOTD_REVIEW_WINDOW_DAYS + \
            settings.IOTD_JUDGEMENT_WINDOW_DAYS

        return self.model.objects.filter(
            user=self.request.user,
            image__submitted_for_iotd_tp_consideration__gte=datetime.now() - timedelta(days=max_days)
        )

    def create(self, request, *args, **kwargs):
        try:
            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseForbidden(e.messages)

