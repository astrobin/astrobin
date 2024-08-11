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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        request_user = self.context['request'].user

        if not request_user.is_authenticated or request_user.userprofile != instance.user:
            for field in ['lat_min', 'lat_sec', 'lon_min', 'lon_sec']:
                representation.pop(field, None)

        return representation

    class Meta:
        model = Location
        fields = '__all__'
