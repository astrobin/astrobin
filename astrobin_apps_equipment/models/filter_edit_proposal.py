from django.db import models

from astrobin_apps_equipment.models import Filter
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin
from astrobin_apps_equipment.models.filter_base_model import FilterBaseModel


class FilterEditProposal(FilterBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Filter, on_delete=models.CASCADE, related_name="edit_proposals")

    def get_absolute_url(self):
        return self.get_absolute_url_base('filter')

    class Meta(FilterBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False