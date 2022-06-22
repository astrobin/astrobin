from django.db import models

from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraBaseModel
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin


class CameraEditProposal(CameraBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="edit_proposals")

    # We need to override this, lest 'self' refers to the *EditProposal model instead of the actual model
    variant_of = models.ForeignKey(
        Camera,
        null=True,
        blank=True,
        related_name='variants_in_edit_proposals',
        on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return self.get_absolute_url_base('camera')

    class Meta(CameraBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False
