from datetime import timedelta

from annoying.functions import get_object_or_None
from celery import shared_task
from django.contrib.auth.models import User
from django.utils import timezone

from astrobin.models import GearMigrationStrategy
from astrobin.services.gear_service import GearService
from astrobin_apps_equipment.models import (
    Accessory, AccessoryEditProposal, Camera, CameraEditProposal, Filter, FilterEditProposal, Mount,
    MountEditProposal,
    Software, SoftwareEditProposal, Telescope,
    TelescopeEditProposal,
)
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass, EquipmentItemUsageType
from astrobin_apps_equipment.services import EquipmentService


@shared_task(time_limit=300)
def expire_equipment_locks():
    expiration_minutes = 30

    for Model in (Telescope, Camera, Mount, Filter, Accessory, Software):
        Model.objects.filter(
            reviewer_lock__isnull=False,
            reviewer_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            reviewer_lock=None,
            reviewer_lock_timestamp=None
        )
        Model.objects.filter(
            edit_proposal_lock__isnull=False,
            edit_proposal_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            edit_proposal_lock=None,
            edit_proposal_lock_timestamp=None
        )

    for Model in (
        TelescopeEditProposal,
        CameraEditProposal,
        MountEditProposal,
        FilterEditProposal,
        AccessoryEditProposal,
        SoftwareEditProposal
    ):
        Model.objects.filter(
            edit_proposal_review_lock__isnull=False,
            edit_proposal_review_lock_timestamp__lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            edit_proposal_review_lock=None,
            edit_proposal_review_lock_timestamp=None
        )


@shared_task(time_limit=30 * 60, acks_late=True)
def approve_migration_strategy(migration_strategy_id: int, moderator_id: int):
    migration_strategy: GearMigrationStrategy = get_object_or_None(GearMigrationStrategy, id=migration_strategy_id)
    moderator: User = get_object_or_None(User, id=moderator_id)

    if migration_strategy and moderator:
        GearService.approve_migration_strategy(migration_strategy, moderator)


@shared_task(time_limit=30 * 60, acks_late=True)
def reject_item(
        item_id: int,
        klass: EquipmentItemKlass,
        reviewer_id: int,
        reason: str,
        comment: str,
        duplicate_of_klass: EquipmentItemKlass,
        duplicate_of_usage_type: EquipmentItemUsageType,
        duplicate_of: int
):
    ModelClass = {
        EquipmentItemKlass.TELESCOPE: Telescope,
        EquipmentItemKlass.CAMERA: Camera,
        EquipmentItemKlass.MOUNT: Mount,
        EquipmentItemKlass.FILTER: Filter,
        EquipmentItemKlass.ACCESSORY: Accessory,
        EquipmentItemKlass.SOFTWARE: Software
    }.get(klass)

    item: ModelClass = get_object_or_None(ModelClass, id=item_id)

    if item is None:
        return

    reviewer = get_object_or_None(User, id=reviewer_id)

    if reviewer is None:
        return

    EquipmentService.reject_item(
        item,
        reviewer,
        reason,
        comment,
        duplicate_of_klass,
        duplicate_of_usage_type,
        duplicate_of,
    )
