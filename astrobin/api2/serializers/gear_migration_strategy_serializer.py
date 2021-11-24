from rest_framework import serializers

from astrobin.models import Gear, GearMigrationStrategy


class GearMigrationStrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = GearMigrationStrategy
        fields = (
            'pk',
            'gear',
            'user',
            'migration_flag',
            'migration_flag_timestamp',
            'migration_content_type',
            'migration_object_id',
            'migration_flag_moderator',
            'migration_flag_reviewer_lock',
            'migration_flag_reviewer_lock_timestamp',
            'migration_flag_reviewer',
            'migration_flag_reviewer_decision',
        )
