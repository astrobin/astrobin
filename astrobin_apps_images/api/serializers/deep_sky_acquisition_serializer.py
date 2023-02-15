from rest_framework import serializers

from astrobin.models import DeepSky_Acquisition


class DeepSkyAcquisitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeepSky_Acquisition
        fields = '__all__'
