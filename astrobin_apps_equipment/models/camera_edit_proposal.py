from django.db import models

from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraBaseModel
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin


class CameraEditProposal(CameraBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="edit_proposals")

    def get_absolute_url(self):
        return self.get_absolute_url_base('camera')

    class Meta(CameraBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False
