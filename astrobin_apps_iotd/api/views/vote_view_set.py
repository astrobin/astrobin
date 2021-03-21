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

from astrobin_apps_iotd.api.serializers.vote_serializer import VoteSerializer
from astrobin_apps_iotd.models import IotdVote


class VoteViewSet(viewsets.ModelViewSet):
    serializer_class = VoteSerializer
    renderer_classes = [BrowsableAPIRenderer, CamelCaseJSONRenderer]
    pagination_class = None
    permission_classes = [IsAuthenticated]
    model = IotdVote

    def get_queryset(self):
        return self.model.objects.filter(
            reviewer=self.request.user,
            date__contains=datetime.now().date())

    def create(self, request, *args, **kwargs):
        try:
            return super(viewsets.ModelViewSet, self).create(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseForbidden(e.messages)

    def destroy(self, request, *args, **kwargs):
        vote = self.get_object()  # type: IotdVote
        deadline = datetime.now() - timedelta(days=settings.IOTD_REVIEW_WINDOW_DAYS)

        if vote.reviewer != request.user:
            return HttpResponseForbidden(["You cannot delete another user's vote."])

        if vote.date < deadline or vote.image.published < deadline:
            return HttpResponseForbidden([_("Sorry, it's now too late to retract this vote.")])

        return super(viewsets.ModelViewSet, self).destroy(request, *args, **kwargs)
