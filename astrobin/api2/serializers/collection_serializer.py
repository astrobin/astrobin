from rest_framework import serializers

from astrobin.models import Collection, Location


class CollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = '__all__'
