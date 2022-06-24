from django.db import models
from safedelete.models import SafeDeleteModel


class DeepSkyAcquisitionMigrationRecord(SafeDeleteModel):
    deep_sky_acquisition = models.ForeignKey(
        'astrobin.DeepSky_Acquisition',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records',
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    from_gear = models.ForeignKey(
        'astrobin.Filter',
        editable=False,
        on_delete=models.CASCADE,
        related_name='deep_sky_acquisition_migration_records_as_from',
    )

    to_item = models.ForeignKey(
        'astrobin_apps_equipment.Filter',
        editable=False,
        on_delete=models.CASCADE,
        related_name='deep_sky_acquisition_migration_records_as_to',
    )

    class Meta:
        unique_together = ('deep_sky_acquisition', 'from_gear', 'deleted')
