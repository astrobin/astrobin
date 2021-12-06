from rest_framework import serializers

from astrobin.models import Gear


class GearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = (
            'pk',
            'make',
            'name',
            'migration_flag_moderator_lock',
            'migration_flag_moderator_lock_timestamp',
        )
