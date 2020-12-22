from rest_framework import serializers

from astrobin.models import Camera


class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = (
            'pk',
            'make',
            'name',
        )
