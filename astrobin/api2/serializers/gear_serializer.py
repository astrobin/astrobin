from rest_framework import serializers

from astrobin.models import Camera, Gear


class GearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = (
            'pk',
            'make',
            'name',
        )
