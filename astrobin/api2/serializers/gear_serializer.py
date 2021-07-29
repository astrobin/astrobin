from rest_framework import serializers

from astrobin.models import Camera, Gear


class GearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = (
            'pk',
            'make',
            'name',
            'migration_flag',
            'migration_flag_moderator',
            'migration_flag_timestamp',
            'migration_content_type',
            'migration_object_id',
        )
