from rest_framework import serializers

from astrobin_apps_iotd.models import IotdReviewerSeenImage
from common.mixins import RequestUserRestSerializerMixin


class ReviewerSeenImageSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdReviewerSeenImage
        fields = (
            'id',
            'user',
            'image',
            'created',
        )
