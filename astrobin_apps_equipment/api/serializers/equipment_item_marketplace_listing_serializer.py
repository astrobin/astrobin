from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_marketplace_listing_line_item_read_serializer import \
    EquipmentItemMarketplaceListingLineItemReadSerializer
from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing


class EquipmentItemMarketplaceListingSerializer(serializers.ModelSerializer):
    line_items = EquipmentItemMarketplaceListingLineItemReadSerializer(many=True, read_only=True)

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceListing
        fields = '__all__'
        read_only_fields = [
            'id',
            'hash',
            'user',
            'created',
            'updated',
        ]
