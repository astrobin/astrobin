from rest_framework import serializers

from astrobin.models import SolarSystem_Acquisition
from astrobin.moon import MoonPhase


class SolarSystemAcquisitionSerializer(serializers.ModelSerializer):
    moon_illumination = serializers.SerializerMethodField()

    def get_moon_illumination(self, obj: SolarSystem_Acquisition):
        return MoonPhase(obj.date).illuminated if obj.date else None

    class Meta:
        model = SolarSystem_Acquisition
        fields = '__all__'
