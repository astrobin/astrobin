from django.db import models

from astrobin_apps_equipment.models import MigrationRecordBaseModel


class MountMigrationRecord(MigrationRecordBaseModel):
    from_gear = models.ForeignKey(
        'astrobin.Mount',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_from',
    )

    to_item = models.ForeignKey(
        'astrobin_apps_equipment.Mount',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_to',
    )

    class Meta(MigrationRecordBaseModel.Meta):
        abstract = False
        unique_together = ('image', 'from_gear')
