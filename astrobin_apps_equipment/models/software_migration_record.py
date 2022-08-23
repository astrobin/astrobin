from django.db import models

from astrobin_apps_equipment.models import MigrationRecordBaseModel


class SoftwareMigrationRecord(MigrationRecordBaseModel):
    from_gear = models.ForeignKey(
        'astrobin.Software',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_from',
    )

    to_item = models.ForeignKey(
        'astrobin_apps_equipment.Software',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_to',
        null=True,
        blank=True,
    )

    class Meta(MigrationRecordBaseModel.Meta):
        abstract = False
        unique_together = ('image', 'from_gear', 'deleted')

