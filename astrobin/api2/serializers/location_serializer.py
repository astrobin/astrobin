from rest_framework import serializers

from astrobin.models import Location


class LocationSerializer(serializers.ModelSerializer):
    # We need to identify elements in the list using their primary key, so use a writable field here, rather than the
    # default which would be read-only.
    id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user.userprofile
        return super().create(validated_data)

    class Meta:
        model = Location
        fields = '__all__'
