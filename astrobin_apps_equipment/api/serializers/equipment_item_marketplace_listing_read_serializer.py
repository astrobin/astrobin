from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing


class EquipmentItemMarketplaceListingReadSerializer(EquipmentItemMarketplaceListingSerializer):
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True)

    class Meta(EquipmentItemMarketplaceListingSerializer.Meta):
        pass
