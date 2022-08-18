from django.db import models

from astrobin_apps_equipment.models import MigrationRecordBaseModel
from astrobin_apps_equipment.models import MIGRATION_USAGE_TYPE_CHOICES


class TelescopeMigrationRecord(MigrationRecordBaseModel):
    from_gear = models.ForeignKey(
        'astrobin.Telescope',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_from',
    )

    to_item = models.ForeignKey(
        'astrobin_apps_equipment.Telescope',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_to',
        null=True,
        blank=True,
    )

    usage_type = models.CharField(
        max_length=16,
        null=False,
        blank=False,
        choices=MIGRATION_USAGE_TYPE_CHOICES
    )

    class Meta(MigrationRecordBaseModel.Meta):
        abstract = False
        unique_together = ('image', 'from_gear', 'usage_type', 'deleted')
