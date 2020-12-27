from rest_framework import serializers

from astrobin_apps_iotd.models import IotdSubmission


class SubmissionSerializer(serializers.ModelSerializer):
    submitter = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    class Meta:
        model = IotdSubmission
        fields = (
            'id',
            'submitter',
            'image',
            'date',
        )
