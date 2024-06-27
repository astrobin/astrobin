from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplacePrivateConversation


class EquipmentItemMarketplacePrivateConversationSerializer(serializers.ModelSerializer):
    user_display_name = serializers.SerializerMethodField(read_only=True)
    total_messages = serializers.SerializerMethodField(read_only=True)
    unread_messages = serializers.SerializerMethodField(read_only=True)
    last_message_timestamp = serializers.SerializerMethodField(read_only=True)

    def get_user_display_name(self, obj: EquipmentItemMarketplacePrivateConversation) -> str:
        return obj.user.userprofile.get_display_name()

    def get_total_messages(self, obj: EquipmentItemMarketplacePrivateConversation) -> int:
        return obj.comments.count()

    def get_unread_messages(self, obj: EquipmentItemMarketplacePrivateConversation) -> int:
        user = self.context['request'].user

        if user == obj.listing.user:
            if obj.listing_user_last_accessed is None:
                count = obj.comments.count()
            else:
                count = obj.comments.filter(created__gt=obj.listing_user_last_accessed).count()
        else:
            if obj.user_last_accessed is None:
                count = obj.comments.count()
            else:
                count = obj.comments.filter(created__gt=obj.user_last_accessed).count()

        return count

    def get_last_message_timestamp(self, obj: EquipmentItemMarketplacePrivateConversation) -> str:
        last_comment = obj.comments.last()
        return last_comment.created if last_comment else None

    class Meta:
        model = EquipmentItemMarketplacePrivateConversation
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created', 'listing']
