from django.db import models

from astrobin_apps_equipment.models import Accessory
from astrobin_apps_equipment.models.accessory_base_model import AccessoryBaseModel
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin


class AccessoryEditProposal(AccessoryBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Accessory, on_delete=models.CASCADE, related_name="edit_proposals")

    def get_absolute_url(self):
        return self.get_absolute_url_base('accessory')

    class Meta(AccessoryBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False
