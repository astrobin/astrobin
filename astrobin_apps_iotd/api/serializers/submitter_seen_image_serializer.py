from rest_framework import serializers

from astrobin_apps_iotd.models import IotdSubmitterSeenImage
from common.mixins import RequestUserRestSerializerMixin


class SubmitterSeenImageSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdSubmitterSeenImage
        fields = (
            'id',
            'user',
            'image',
            'created',
        )
