from rest_framework import serializers

from astrobin.models import Collection


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        exclude = ['images']
