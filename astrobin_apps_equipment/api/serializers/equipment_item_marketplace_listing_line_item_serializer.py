from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListingLineItem


class EquipmentItemMarketplaceListingLineItemSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceListingLineItem
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
