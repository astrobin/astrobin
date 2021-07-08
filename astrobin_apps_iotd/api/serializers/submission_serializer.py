from rest_framework import serializers

from astrobin_apps_iotd.models import IotdSubmission


class SubmissionSerializer(serializers.ModelSerializer):
    submitter = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    def create(self, validated_data):
        if 'submitter' not in validated_data:
            validated_data['submitter'] = self.context['request'].user
        return super(SubmissionSerializer, self).create(validated_data)

    class Meta:
        model = IotdSubmission
        fields = (
            'id',
            'submitter',
            'image',
            'date',
        )
