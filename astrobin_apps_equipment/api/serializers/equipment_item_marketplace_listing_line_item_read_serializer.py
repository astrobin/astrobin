from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_image_serializer import \
    EquipmentItemMarketplaceListingLineItemImageSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_serializer import \
    EquipmentItemMarketplaceListingLineItemSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_offer_serializer import \
    EquipmentItemMarketplaceOfferSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem


class EquipmentItemMarketplaceListingLineItemReadSerializer(EquipmentItemMarketplaceListingLineItemSerializer):
    images = EquipmentItemMarketplaceListingLineItemImageSerializer(many=True)
    offers = EquipmentItemMarketplaceOfferSerializer(many=True)

    def to_representation(self, instance: EquipmentItemMarketplaceListingLineItem):
        data = super().to_representation(instance)
        user = self.context['request'].user

        if user == instance.user:
            offers = instance.offers.all()
        elif user.is_authenticated:
            offers = instance.offers.filter(user=user)
        else:
            offers = instance.offers.none()

        data['offers'] = EquipmentItemMarketplaceOfferSerializer(offers, many=True).data
        data['images'] = EquipmentItemMarketplaceListingLineItemImageSerializer(
            instance.images.all().order_by('position', '-created'), many=True
        ).data

        return data

    class Meta(EquipmentItemMarketplaceListingLineItemSerializer.Meta):
        pass
