from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from astrobin_apps_equipment.models import (
    Accessory, AccessoryEditProposal, Camera, CameraEditProposal, Filter, FilterEditProposal, Mount, MountEditProposal,
    Software, SoftwareEditProposal, Telescope,
    TelescopeEditProposal,
)


@shared_task(time_limit=30)
def expire_equipment_locks():
    expiration_minutes = 10

    for Model in (Telescope, Camera, Mount, Filter, Accessory, Software):
        Model.objects.filter(
            reviewer_lock__isnull=False,
            reviewer_lock_timestamp_lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            reviewer_lock=None,
            reviewer_lock_timestamp=None
        )

        Model.objects.filter(
            edit_proposal_lock__isnull=False,
            edit_proposal_lock_timestamp_lt=timezone.now() - timedelta(minutes=expiration_minutes)
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
            edit_proposal_review_lock_timestamp_lt=timezone.now() - timedelta(minutes=expiration_minutes)
        ).update(
            edit_proposal_review_lock=None,
            edit_proposal_review_lock_timestamp=None
        )
