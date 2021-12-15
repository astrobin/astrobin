from rest_framework import serializers

from astrobin.api2.serializers.camera_serializer import CameraSerializer
from astrobin.api2.serializers.telescope_serializer import TelescopeSerializer
from astrobin.models import Image


class ReviewQueueSerializer(serializers.ModelSerializer):
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    imaging_telescopes = TelescopeSerializer(many=True, read_only=True)
    imaging_cameras = CameraSerializer(many=True, read_only=True)

    class Meta:
        model = Image
        fields = (
            'user',
            'pk',
            'hash',
            'title',
            'image_file',
            'w',
            'h',
            'imaging_telescopes',
            'imaging_cameras',
            'published',
        )
