# -*- coding: utf-8 -*-


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

from astrobin_apps_iotd.api.serializers.hidden_image_serializer import HiddenImageSerializer
from astrobin_apps_iotd.models import IotdHiddenImage
from common.constants import GroupName
from common.permissions import is_group_member


class HiddenImageViewSet(viewsets.ModelViewSet):
    serializer_class = HiddenImageSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [
        IsAuthenticated,
        is_group_member([GroupName.IOTD_SUBMITTERS, GroupName.IOTD_REVIEWERS, GroupName.IOTD_JUDGES])
    ]
    model = IotdHiddenImage

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
        except IntegrityError:
            return Response(status=204)

    def destroy(self, request, *args, **kwargs):
        object = self.get_object()  # type: IotdHiddenImage

        if object.user != request.user:
            return HttpResponseForbidden(["You cannot unhide an image on behalf of another user."])

        return super(viewsets.ModelViewSet, self).destroy(request, *args, **kwargs)
