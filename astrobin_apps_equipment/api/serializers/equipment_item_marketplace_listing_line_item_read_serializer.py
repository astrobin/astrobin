from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer


class EquipmentItemMarketplaceListingLineItemReadSerializer(EquipmentItemMarketplaceListingLineItemSerializer):
    images = EquipmentItemMarketplaceListingLineItemImageSerializer(many=True)

    class Meta(EquipmentItemMarketplaceListingLineItemSerializer.Meta):
        pass
