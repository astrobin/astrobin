from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer


class EquipmentItemMarketplaceListingReadSerializer(EquipmentItemMarketplaceListingSerializer):
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True)

    class Meta(EquipmentItemMarketplaceListingSerializer.Meta):
        pass
