# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer

from astrobin_apps_iotd.api.serializers.submission_serializer import SubmissionSerializer
from astrobin_apps_iotd.models import IotdSubmission


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated]
    model = IotdSubmission

    def get_queryset(self):
        return self.model.objects.filter(
            submitter=self.request.user,
            date__gte=datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS))

    def create(self, request, *args, **kwargs):
        try:
            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseForbidden(e.messages)
