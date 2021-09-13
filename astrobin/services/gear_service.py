class GearService:
    """ Service related to the legacy models.Gear object """

    @staticmethod
    def reset_migration_fields(queryset):
        queryset.update(
            migration_flag=None,
            migration_flag_timestamp=None,
            migration_content_type=None,
            migration_object_id=None,
            migration_flag_moderator=None,
            migration_flag_moderator_lock=None,
            migration_flag_moderator_lock_timestamp=None,
            migration_flag_reviewer=None,
            migration_flag_reviewer_lock=None,
            migration_flag_reviewer_lock_timestamp=None,
            migration_flag_reviewer_decision=None,
            migration_flag_reviewer_rejection_comment=None
        )
