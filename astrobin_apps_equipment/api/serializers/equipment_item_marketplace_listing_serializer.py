from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing


class EquipmentItemMarketplaceListingSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceListing
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'updated']
