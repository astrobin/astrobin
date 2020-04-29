# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets

from astrobin_apps_contests.api.serializers import ContestSerializer
from astrobin_apps_contests.models import Contest
from common.permissions import IsAdminUserOrReadOnly


class ContestViewSet(viewsets.ModelViewSet):
    serializer_class = ContestSerializer
    queryset = Contest.objects.all()
    permission_classes = [IsAdminUserOrReadOnly]
