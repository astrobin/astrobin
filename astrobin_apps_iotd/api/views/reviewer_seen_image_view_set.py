# -*- coding: utf-8 -*-


from datetime import datetime, timedelta

from annoying.functions import get_object_or_None
from django.conf import settings
from django.db import IntegrityError
from django.db.models import QuerySet
from django.http import HttpResponseForbidden
from djangorestframework_camel_case.render import CamelCaseJSONRenderer
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response

from astrobin.models import Image
from astrobin_apps_iotd.api.serializers.reviewer_seen_image_serializer import ReviewerSeenImageSerializer
from astrobin_apps_iotd.models import IotdReviewerSeenImage
from common.constants import GroupName
from common.permissions import is_group_member


class ReviewerSeenImageViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewerSeenImageSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated, is_group_member(GroupName.IOTD_REVIEWERS)]
    model = IotdReviewerSeenImage
    http_method_names = ['get', 'head', 'options', 'post']

    def get_queryset(self) -> QuerySet:
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
            image = Image.objects.get(id=request.data.get('image'))
            user = request.user

            seen_object = get_object_or_None(IotdReviewerSeenImage, image=image, user=user)

            if seen_object:
                return Response(self.serializer_class(seen_object).data, status=200)

            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except IntegrityError:
            return Response(status=204)
        except Exception as e:
            return HttpResponseForbidden(str(e))

