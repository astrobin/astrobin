from rest_framework import serializers

from astrobin_apps_iotd.models import IotdDismissedImage


class DismissedImageSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdDismissedImage
        fields = (
            'id',
            'user',
            'image',
            'created',
        )
