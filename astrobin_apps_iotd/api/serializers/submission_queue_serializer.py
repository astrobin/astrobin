from rest_framework import serializers

from astrobin.models import Image


class SubmissionQueueSerializer(serializers.ModelSerializer):
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    imaging_telescopes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    imaging_cameras = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

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
