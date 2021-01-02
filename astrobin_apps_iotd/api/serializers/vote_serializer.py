from rest_framework import serializers

from astrobin_apps_iotd.models import IotdVote


class VoteSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdVote
        fields = (
            'id',
            'reviewer',
            'image',
            'date',
        )
