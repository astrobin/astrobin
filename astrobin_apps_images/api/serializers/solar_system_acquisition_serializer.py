from rest_framework import serializers

from astrobin.models import SolarSystem_Acquisition


class SolarSystemAcquisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolarSystem_Acquisition
        fields = '__all__'
