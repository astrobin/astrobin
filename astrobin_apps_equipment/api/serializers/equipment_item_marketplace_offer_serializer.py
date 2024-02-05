from rest_framework import serializers

from astrobin_apps_equipment.models import (
    EquipmentItemMarketplaceListing, EquipmentItemMarketplaceListingLineItem,
    EquipmentItemMarketplaceOffer,
)
from common.mixins import RequestUserRestSerializerMixin


class EquipmentItemMarketplaceOfferSerializer(RequestUserRestSerializerMixin, serializers.ModelSerializer):
    listing = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListing.objects.all())
    line_item = serializers.PrimaryKeyRelatedField(queryset=EquipmentItemMarketplaceListingLineItem.objects.all())

    class Meta:
        model = EquipmentItemMarketplaceOffer
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
