from typing import Optional

from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceFeedback
from astrobin_apps_equipment.services.marketplace_service import MarketplaceService


class EquipmentItemMarketplaceFeedbackSerializer(serializers.ModelSerializer):
    marketplace_feedback = serializers.SerializerMethodField(read_only=True)
    marketplace_feedback_count = serializers.SerializerMethodField(read_only=True)

    def get_marketplace_feedback(self, feedback: EquipmentItemMarketplaceFeedback) -> Optional[int]:
        return MarketplaceService.calculate_received_feedback_score(feedback.recipient)

    def get_marketplace_feedback_count(self, feedback: EquipmentItemMarketplaceFeedback) -> Optional[int]:
        return MarketplaceService.received_feedback_count(feedback.recipient)

    def create(self, validated_data):
        user = self.context['request'].user
        line_item_id = self.context['request'].data.get('line_item')

        validated_data['user'] = user
        validated_data['line_item_id'] = line_item_id

        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceFeedback
        fields = '__all__'
