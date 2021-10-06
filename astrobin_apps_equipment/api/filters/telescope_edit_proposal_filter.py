from astrobin_apps_equipment.api.filters.equipment_item_edit_proposal_filter import EquipmentItemEditProposalFilter
from astrobin_apps_equipment.models import CameraEditProposal


class TelescopeEditProposalFilter(EquipmentItemEditProposalFilter):
    class Meta(EquipmentItemEditProposalFilter.Meta):
        model = CameraEditProposal
