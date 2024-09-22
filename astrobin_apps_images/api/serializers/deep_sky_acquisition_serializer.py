from rest_framework import serializers

from astrobin.models import DeepSky_Acquisition
from astrobin.moon import MoonPhase


class DeepSkyAcquisitionSerializer(serializers.ModelSerializer):
    filter_make = serializers.CharField(source='filter.make', read_only=True)
    filter_name = serializers.CharField(source='filter.name', read_only=True)
    filter_type = serializers.CharField(source='filter.type', read_only=True)

    filter_2_brand = serializers.CharField(source='filter_2.brand', read_only=True)
    filter_2_name = serializers.CharField(source='filter_2.name', read_only=True)
    filter_2_type = serializers.CharField(source='filter_2.type', read_only=True)

    moon_illumination = serializers.SerializerMethodField()

    def get_moon_illumination(self, obj: DeepSky_Acquisition):
        return MoonPhase(obj.date).illuminated if obj.date else None

    class Meta:
        model = DeepSky_Acquisition
        fields = '__all__'
