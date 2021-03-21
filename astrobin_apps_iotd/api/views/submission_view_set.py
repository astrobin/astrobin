# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
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
            date__contains=datetime.now().date())

    def create(self, request, *args, **kwargs):
        try:
            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseForbidden(e.messages)

    def destroy(self, request, *args, **kwargs):
        submission = self.get_object()  # type: IotdSubmission
        deadline = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)

        if submission.submitter != request.user:
            return HttpResponseForbidden(["You cannot delete another user's submission."])

        if submission.date < deadline or submission.image.published < deadline:
            return HttpResponseForbidden([_("Sorry, it's now too late to retract this submission.")])

        return super(viewsets.ModelViewSet, self).destroy(request, *args, **kwargs)
