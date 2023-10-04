from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing


class EquipmentItemMarketplaceListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemMarketplaceListing
        fields = '__all__'
        depth = 1
