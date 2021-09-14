from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class EquipmentItemEditProposalViewSet(EquipmentItemViewSet):
    class Meta(EquipmentItemViewSet.Meta):
        abstract = True
