from rest_framework import serializers

from astrobin_apps_iotd.models import IotdHiddenImage


class HiddenImageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdHiddenImage
        fields = (
            'id',
            'user',
            'image',
            'created',
        )
