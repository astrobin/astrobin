from django.db import models

from astrobin_apps_equipment.models import Telescope
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin
from astrobin_apps_equipment.models.telescope_base_model import TelescopeBaseModel


class TelescopeEditProposal(TelescopeBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Telescope, on_delete=models.CASCADE, related_name="edit_proposals")

    class Meta(TelescopeBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False
