from astrobin_apps_equipment.api.serializers.equipment_item_image_serializer import EquipmentItemImageSerializer
from astrobin_apps_equipment.models.filter_edit_proposal import FilterEditProposal


class FilterEditProposalImageSerializer(EquipmentItemImageSerializer):
    class Meta(EquipmentItemImageSerializer.Meta):
        model = FilterEditProposal
        abstract = False
