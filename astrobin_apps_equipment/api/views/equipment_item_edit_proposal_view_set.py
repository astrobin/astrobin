from rest_framework.permissions import IsAuthenticatedOrReadOnly

from astrobin_apps_equipment.api.views.equipment_item_view_set import EquipmentItemViewSet


class EquipmentItemEditProposalViewSet(EquipmentItemViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]

    class Meta(EquipmentItemViewSet.Meta):
        abstract = True
