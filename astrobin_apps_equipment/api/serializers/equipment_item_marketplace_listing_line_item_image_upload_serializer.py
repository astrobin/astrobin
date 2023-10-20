from rest_framework import serializers

from astrobin_apps_equipment.models.equipment_item_marketplace_listing_line_item_image import \
    EquipmentItemMarketplaceListingLineItemImage
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceListingLineItemImageUploadSerializer(
    RequestUserRestSerializerMixin, serializers.ModelSerializer
):
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceListingLineItemImage
        fields = '__all__'
