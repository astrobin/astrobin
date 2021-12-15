from rest_framework import serializers

from astrobin.api2.serializers.camera_serializer import CameraSerializer
from astrobin.api2.serializers.telescope_serializer import TelescopeSerializer
from astrobin.models import Image


class BaseQueueSerializer(serializers.ModelSerializer):
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    imaging_telescopes = TelescopeSerializer(many=True, read_only=True)
    imaging_cameras = CameraSerializer(many=True, read_only=True)

    def to_representation(self, instance: Image):
        representation = super().to_representation(instance)
        representation.update(
            {
                'thumbnails': [
                    {
                        'alias': alias,
                        'id': instance.pk,
                        'revision': 'final',
                        'url': instance.thumbnail(alias, None, sync=True)
                    } for alias in ('story', 'regular', 'hd', 'hd_anonymized')
                ]
            }
        )
        return representation

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
