from rest_framework import serializers

from astrobin.models import Image


class SubmissionQueueSerializer(serializers.HyperlinkedModelSerializer):
    hash = serializers.PrimaryKeyRelatedField(read_only=True)
    w = serializers.IntegerField()
    h = serializers.IntegerField()

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
        )
