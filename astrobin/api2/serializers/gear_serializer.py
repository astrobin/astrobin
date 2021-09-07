from rest_framework import serializers

from astrobin.models import Gear


class GearSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gear
        fields = (
            'pk',
            'make',
            'name',
            'migration_flag',
            'migration_flag_timestamp',
            'migration_content_type',
            'migration_object_id',
            'migration_flag_moderator',
            'migration_flag_moderator_lock',
            'migration_flag_moderator_lock_timestamp',
            'migration_flag_reviewer',
            'migration_flag_reviewer_lock',
            'migration_flag_reviewer_lock_timestamp',
            'migration_flag_reviewer_decision',
            'migration_flag_reviewer_rejection_comment',
        )
