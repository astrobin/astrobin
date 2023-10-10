from rest_framework import serializers

from astrobin_apps_equipment.models.equipment_item_marketplace_listing_image import EquipmentItemMarketplaceListingImage
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceListingImageUploadSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemMarketplaceListingImage
        fields = '__all__'
