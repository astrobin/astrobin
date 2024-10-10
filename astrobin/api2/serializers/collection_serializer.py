from typing import Optional

from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()
    image_count = serializers.SerializerMethodField()

    def get_cover_thumbnail(self, instance: Collection) -> Optional[str]:
        if instance.cover:
            return instance.cover.thumbnail('regular', None, sync=True)
        return None

    def get_image_count(self, instance: Collection) -> int:
        if self.context.get('request').user == instance.user:
            return instance.images.count()
        return instance.images.filter(is_wip=False).count()

    class Meta:
        model = Collection
        exclude = ['images']
