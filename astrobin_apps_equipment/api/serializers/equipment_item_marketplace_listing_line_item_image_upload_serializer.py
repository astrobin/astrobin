from rest_framework import serializers

from astrobin_apps_equipment.models.equipment_item_marketplace_listing_line_item_image import \
    EquipmentItemMarketplaceListingLineItemImage
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceListingLineItemImageUploadSerializer(
    RequestUserRestSerializerMixin, serializers.ModelSerializer
):
    class Meta:
        model = EquipmentItemMarketplaceListingLineItemImage
        fields = '__all__'
