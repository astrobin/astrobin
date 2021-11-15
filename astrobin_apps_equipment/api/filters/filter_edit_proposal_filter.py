from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal

from astrobin_apps_equipment.api.filters.equipment_item_edit_proposal_filter import EquipmentItemEditProposalFilter


class FilterEditProposalFilter(EquipmentItemEditProposalFilter):
    class Meta(EquipmentItemEditProposalFilter.Meta):
        model = FilterEditProposal
