from rest_framework import serializers

from astrobin.models import DeepSky_Acquisition


class DeepSkyAcquisitionSerializer(serializers.ModelSerializer):
    filter_make = serializers.CharField(source='filter.make', read_only=True)
    filter_name = serializers.CharField(source='filter.name', read_only=True)
    filter_type = serializers.CharField(source='filter.type', read_only=True)

    filter_2_brand = serializers.CharField(source='filter_2.brand', read_only=True)
    filter_2_name = serializers.CharField(source='filter_2.name', read_only=True)
    filter_2_type = serializers.CharField(source='filter_2.type', read_only=True)

    class Meta:
        model = DeepSky_Acquisition
        fields = '__all__'
