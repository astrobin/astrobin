# Third party apps
from rest_framework import serializers

# This app
from .models import RawImage


class RawImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawImage
        fields = ('file',)
        read_only_fields = (
            'user',
            'original_filename',
            'size',
            'uploaded',
            'indexed',
            'active',
            'image_type',
            'acquisition_date',
            'camera',
            'temperature',
        )
