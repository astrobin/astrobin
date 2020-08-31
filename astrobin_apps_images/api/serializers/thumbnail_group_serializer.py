from rest_framework import serializers

from astrobin_apps_images.models import ThumbnailGroup


class ThumbnailGroupSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ThumbnailGroup
        fields = (
            'pk',
            'image',
            'revision',
            'real',
            'hd',
            'regular',
            'gallery',
            'thumb',
        )
