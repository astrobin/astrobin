from typing import Optional

from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    cover_thumbnail = serializers.SerializerMethodField()

    def get_cover_thumbnail(self, instance: Collection) -> Optional[str]:
        if instance.cover:
            return instance.cover.thumbnail('regular', None, sync=True)
        return None

    class Meta:
        model = Collection
        exclude = ['images']
