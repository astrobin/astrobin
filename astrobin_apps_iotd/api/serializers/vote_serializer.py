from rest_framework import serializers

from astrobin_apps_iotd.models import IotdVote


class VoteSerializer(serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        if 'reviewer' not in validated_data:
            validated_data['reviewer'] = self.context['request'].user
        return super(VoteSerializer, self).create(validated_data)

    class Meta:
        model = IotdVote
        fields = (
            'id',
            'reviewer',
            'image',
            'date',
        )
