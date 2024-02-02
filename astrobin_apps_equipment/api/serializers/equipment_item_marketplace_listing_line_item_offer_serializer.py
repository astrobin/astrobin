from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceOffer
from astrobin_apps_equipment.models.equipment_item_marketplace_listing_line_item_image import \
    EquipmentItemMarketplaceListingLineItemImage
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceOfferSerializer(
    RequestUserRestSerializerMixin, serializers.ModelSerializer
):
    def validate_user(self, value):
        return self.context['request'].user

    class Meta:
        model = EquipmentItemMarketplaceOffer
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
