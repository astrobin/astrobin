# -*- coding: utf-8 -*-

from rest_framework import viewsets

from astrobin_apps_iotd.api.serializers.stats_serializer import StatsSerializer
from common.permissions import ReadOnly


class StatsViewSet(viewsets.ModelViewSet):
    serializer_class = StatsSerializer
    permission_classes = [ReadOnly]

    def get_queryset(self):
        return self.serializer_class.Meta.model.objects.all()
