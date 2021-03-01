from rest_framework import serializers

from astrobin.models import ImageRevision, Image


class ImageRevisionUploadSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.PrimaryKeyRelatedField(queryset=Image.objects_including_wip)
    label = serializers.CharField(max_length=2)
    is_final = serializers.BooleanField(default=False)
    w = serializers.IntegerField()
    h = serializers.IntegerField()
    uploader_in_progress = serializers.NullBooleanField()

    class Meta:
        model = ImageRevision
        fields = (
            'pk',
            'uploaded',
            'image',
            'image_file',
            'description',
            'skip_notifications',
            'label',
            'is_final',
            'w',
            'h',
            'uploader_in_progress',
        )
