from typing import Optional

from rest_framework import serializers

from astrobin.models import Collection, Image


class CollectionAddRemoveImagesSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    def get_images(self, instance: Collection) -> Optional[str]:
        if self.context.get('request').user == instance.user:
            return Image.objects_including_wip_plain.filter(collections=instance).values_list('pk', flat=True)
        return instance.images.all().values_list('pk', flat=True)

    class Meta:
        model = Collection
        fields = '__all__'
