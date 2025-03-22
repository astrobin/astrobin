from typing import Optional

from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    user_display_name = serializers.CharField(source='user.userprofile.get_display_name', read_only=True)
    display_collections_on_public_gallery = serializers.BooleanField(
        source='user.userprofile.display_collections_on_public_gallery',
        read_only=True
    )

    def get_cover_thumbnail(self, instance: Collection) -> Optional[str]:
        if instance.cover:
            return instance.cover.thumbnail('regular', None, sync=True)

        if instance.images.exists():
            return instance.images.first().thumbnail('regular', None, sync=True)

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
            'username',
            'user_display_name',
            'display_collections_on_public_gallery',
            'images',
            'cover',
            'image_count',
            'image_count_including_wip',
        ]
