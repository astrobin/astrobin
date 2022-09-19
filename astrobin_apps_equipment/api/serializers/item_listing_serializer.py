from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemListing


class ItemListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemListing
        fields = '__all__'
        depth = 1
