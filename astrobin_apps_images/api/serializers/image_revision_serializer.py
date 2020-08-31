from rest_framework import serializers

from astrobin.models import ImageRevision, Image


class ImageRevisionSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.PrimaryKeyRelatedField(queryset=Image.objects_including_wip)
    label = serializers.CharField(max_length=2)
    is_final = serializers.BooleanField(default=False)

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
        )
