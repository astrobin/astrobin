from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_feedback_serializer import \
    EquipmentItemMarketplaceFeedbackSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_serializer import \
    EquipmentItemMarketplaceListingSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing


class EquipmentItemMarketplaceListingReadSerializer(EquipmentItemMarketplaceListingSerializer):
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True)
    feedbacks = EquipmentItemMarketplaceFeedbackSerializer(many=True)

    def to_representation(self, instance: EquipmentItemMarketplaceListing):
        data = super().to_representation(instance)
        user = self.context['request'].user

        if user == instance.user:
            feedbacks = instance.feedbacks.all()
        elif user.is_authenticated:
            feedbacks = instance.feedbacks.filter(user=user)
        else:
            feedbacks = instance.feedbacks.none()

        data['feedbacks'] = EquipmentItemMarketplaceFeedbackSerializer(feedbacks, many=True).data

        return data

    class Meta(EquipmentItemMarketplaceListingSerializer.Meta):
        pass
