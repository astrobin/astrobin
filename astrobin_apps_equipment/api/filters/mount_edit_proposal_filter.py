from astrobin_apps_equipment.api.filters.equipment_item_edit_proposal_filter import EquipmentItemEditProposalFilter
from astrobin_apps_equipment.models.mount_edit_proposal import MountEditProposal


class MountEditProposalFilter(EquipmentItemEditProposalFilter):
    class Meta(EquipmentItemEditProposalFilter.Meta):
        model = MountEditProposal
