from django.db import models

from astrobin_apps_equipment.models import MigrationRecordBaseModel


class FocalReducerMigrationRecord(MigrationRecordBaseModel):
    from_gear = models.ForeignKey(
        'astrobin.FocalReducer',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_as_from',
    )

    to_item = models.ForeignKey(
        'astrobin_apps_equipment.Accessory',
        editable=False,
        on_delete=models.CASCADE,
        related_name='migration_records_from_focal_reducers_as_to',
    )

    class Meta(MigrationRecordBaseModel.Meta):
        pass
