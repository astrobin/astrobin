from rest_framework import viewsets

from astrobin.api2.serializers.location_serializer import LocationSerializer
from astrobin.models import Location


class UserLocationsViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Location.objects.filter(image__user=self.request.user)
        return Location.objects.none()
