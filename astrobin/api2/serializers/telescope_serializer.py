from rest_framework import serializers

from astrobin.models import Telescope


class TelescopeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Telescope
        fields = (
            'pk',
            'make',
            'name',
        )
