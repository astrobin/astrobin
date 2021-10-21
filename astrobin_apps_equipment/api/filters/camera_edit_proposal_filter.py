from astrobin_apps_equipment.api.filters.equipment_item_edit_proposal_filter import EquipmentItemEditProposalFilter
from astrobin_apps_equipment.models import CameraEditProposal


class CameraEditProposalFilter(EquipmentItemEditProposalFilter):
    class Meta(EquipmentItemEditProposalFilter.Meta):
        model = CameraEditProposal
