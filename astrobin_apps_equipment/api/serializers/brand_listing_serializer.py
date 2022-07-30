from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentBrandListing


class BrandListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrandListing
        fields = '__all__'
        depth = 1
