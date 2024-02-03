from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer


class EquipmentItemMarketplaceListingLineItemReadSerializer(EquipmentItemMarketplaceListingLineItemSerializer):
    images = EquipmentItemMarketplaceListingLineItemImageSerializer(many=True)
    offers = EquipmentItemMarketplaceOfferSerializer(many=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)

        if self.context['request'].user == instance.user:
            offers = instance.offers.filter(user=instance.user)
        else:
            offers = instance.offers.all()

        data['offers'] = EquipmentItemMarketplaceOfferSerializer(offers, many=True).data
        return data

    class Meta(EquipmentItemMarketplaceListingLineItemSerializer.Meta):
        pass
