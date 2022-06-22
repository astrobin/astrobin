from django.db import models

from astrobin_apps_equipment.models import Mount
from astrobin_apps_equipment.models.equipment_item_edit_proposal_mixin import EquipmentItemEditProposalMixin
from astrobin_apps_equipment.models.mount_base_model import MountBaseModel


class MountEditProposal(MountBaseModel, EquipmentItemEditProposalMixin):
    edit_proposal_target = models.ForeignKey(Mount, on_delete=models.CASCADE, related_name="edit_proposals")

    # We need to override this, lest 'self' refers to the *EditProposal model instead of the actual model
    variant_of = models.ForeignKey(
        Mount,
        null=True,
        blank=True,
        related_name='variants_in_edit_proposals',
        on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return self.get_absolute_url_base('mount')

    class Meta(MountBaseModel.Meta):
        unique_together = []
        ordering = ['-edit_proposal_created']
        abstract = False
