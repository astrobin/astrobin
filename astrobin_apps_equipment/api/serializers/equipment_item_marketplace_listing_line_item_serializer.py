from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem


class EquipmentItemMarketplaceListingLineItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemMarketplaceListingLineItem
        fields = '__all__'
        depth = 1
