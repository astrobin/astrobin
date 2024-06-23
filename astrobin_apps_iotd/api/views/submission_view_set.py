# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from django.utils.translation import ugettext_lazy as _
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_iotd.api.serializers.submission_serializer import SubmissionSerializer
from astrobin_apps_iotd.models import IotdSubmission
from common.constants import GroupName
from common.permissions import is_group_member


log = logging.getLogger(__name__)


class SubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = SubmissionSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated, is_group_member(GroupName.IOTD_SUBMITTERS)]
    model = IotdSubmission

    def get_queryset(self):
        return self.model.objects.filter(
            submitter=self.request.user,
            date__contains=datetime.now().date())

    def create(self, request, *args, **kwargs):
        try:
            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except ValidationError as e:
            log.error(f"ValidationError with user {request.user} creating IotdSubmission: " + str(e))
            return HttpResponseForbidden(e.messages)
        except IntegrityError:
            return Response(status=204)

    def destroy(self, request, *args, **kwargs):
        submission = self.get_object()  # type: IotdSubmission
        deadline = datetime.now() - timedelta(days=settings.IOTD_SUBMISSION_WINDOW_DAYS)

        if submission.submitter != request.user:
            return HttpResponseForbidden(["You cannot delete another user's submission."])

        if submission.date < deadline or submission.image.submitted_for_iotd_tp_consideration < deadline:
            return HttpResponseForbidden([_("Sorry, it's now too late to retract this submission.")])

        return super(viewsets.ModelViewSet, self).destroy(request, *args, **kwargs)
