from rest_framework import serializers

from astrobin.models import Image


class ImageSerializerTrash(serializers.ModelSerializer):
    def create(self, validated_data):
        raise NotImplementedError

    def update(self, instance, validated_data):
        raise NotImplementedError

    class Meta:
        model = Image
        fields = (
            'pk',
            'hash',
            'title',
            'final_gallery_thumbnail',
            'published',
            'uploaded',
            'deleted',
        )
