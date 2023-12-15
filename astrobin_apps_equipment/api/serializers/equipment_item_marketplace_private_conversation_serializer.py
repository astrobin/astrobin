from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplacePrivateConversation


class EquipmentItemMarketplacePrivateConversationSerializer(serializers.ModelSerializer):
    total_messages = serializers.SerializerMethodField(read_only=True)
    unread_messages = serializers.SerializerMethodField(read_only=True)

    def get_total_messages(self, obj: EquipmentItemMarketplacePrivateConversation) -> int:
        return obj.comments.count()

    def get_unread_messages(self, obj: EquipmentItemMarketplacePrivateConversation) -> int:
        user = self.context['request'].user

        if user == obj.listing.user:
            if obj.listing_user_last_accessed is None:
                count = obj.comments.count()
            else:
                count = obj.comments.filter(created__gt=obj.user_last_accessed).count()
        else:
            count = obj.comments.filter(created__gt=obj.user_last_accessed).count()

        return count

    class Meta:
        model = EquipmentItemMarketplacePrivateConversation
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'listing']
