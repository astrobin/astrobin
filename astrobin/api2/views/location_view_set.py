# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from astrobin.api2.serializers.location_serializer import LocationSerializer
from astrobin.models import Location


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.request.user.is_authenticated():
            return Location.objects.none()

        if not hasattr(self.request.user, 'userprofile'):
            return Location.objects.none()

        return self.request.user.userprofile.location_set.all()
