from typing import Optional

from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceFeedback
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService


class EquipmentItemMarketplaceFeedbackSerializer(serializers.ModelSerializer):
    marketplace_feedback = serializers.SerializerMethodField(read_only=True)
    marketplace_feedback_count = serializers.SerializerMethodField(read_only=True)
    listing_display_name = serializers.SerializerMethodField(read_only=True)
    listing_hash = serializers.SerializerMethodField(read_only=True)
    user_display_name = serializers.SerializerMethodField(read_only=True)
    recipient_display_name = serializers.SerializerMethodField(read_only=True)

    def get_marketplace_feedback(self, feedback: EquipmentItemMarketplaceFeedback) -> Optional[int]:
        return MarketplaceService.calculate_received_feedback_score(feedback.recipient)

    def get_marketplace_feedback_count(self, feedback: EquipmentItemMarketplaceFeedback) -> Optional[int]:
        return MarketplaceService.received_feedback_count(feedback.recipient)

    def get_listing_hash(self, feedback: EquipmentItemMarketplaceFeedback) -> str:
        return feedback.listing.hash

    def get_listing_display_name(self, feedback: EquipmentItemMarketplaceFeedback) -> str:
        return str(feedback.listing)

    def get_user_display_name(self, feedback: EquipmentItemMarketplaceFeedback) -> str:
        return feedback.user.userprofile.get_display_name()

    def get_recipient_display_name(self, feedback: EquipmentItemMarketplaceFeedback) -> str:
        return feedback.recipient.userprofile.get_display_name()

    def create(self, validated_data):
        user = self.context['request'].user
        listing_id = self.context['request'].data.get('listing')

        validated_data['user'] = user
        validated_data['listing_id'] = listing_id

        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceFeedback
        fields = '__all__'
