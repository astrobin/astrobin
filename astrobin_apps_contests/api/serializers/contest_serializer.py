from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from astrobin_apps_contests.models import Contest


class ContestSerializer(serializers.HyperlinkedModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    title = serializers.CharField(validators=[UniqueValidator(queryset=Contest.all_objects.all())])

    class Meta:
        model = Contest
        fields = '__all__'

    def validate(self, data):
        start_date = data['start_date']
        end_date = data['end_date']

        if (end_date - start_date).days < 7:
            raise serializers.ValidationError('CONTEST_MIN_DURATION_VALIDATION_ERROR')

        return data
