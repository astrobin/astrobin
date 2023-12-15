from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceListing, EquipmentItemMarketplacePrivateConversation


class EquipmentItemMarketplacePrivateConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemMarketplacePrivateConversation
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created']
