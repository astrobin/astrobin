# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpResponseForbidden
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin_apps_iotd.api.serializers.dismissed_image_serializer import DismissedImageSerializer
from astrobin_apps_iotd.models import IotdDismissedImage
from common.constants import GroupName
from common.permissions import is_group_member


log = logging.getLogger(__name__)


class DismissedImageViewSet(viewsets.ModelViewSet):
    serializer_class = DismissedImageSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated, is_group_member([GroupName.IOTD_SUBMITTERS, GroupName.IOTD_REVIEWERS])]
    model = IotdDismissedImage
    http_method_names = ['get', 'post', 'head']

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
            log.error(f"ValidationError with user {request.user} creating IotdDismissedImage: " + str(e))
            return HttpResponseForbidden(e.messages)
        except IntegrityError:
            return Response(status=204)
