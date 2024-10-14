from typing import Optional

from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()

    def get_cover_thumbnail(self, instance: Collection) -> Optional[str]:
        if instance.cover:
            return instance.cover.thumbnail('regular', None, sync=True)
        return None

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = Collection
        exclude = ['images']
        read_only_fields = [
            'date_created',
            'date_updated',
            'user',
            'images',
            'cover',
            'image_count',
            'image_count_including_wip',
        ]
