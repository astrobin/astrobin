from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceFeedback


class EquipmentItemMarketplaceFeedbackSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        line_item_id = self.context['request'].data.get('line_item')

        validated_data['user'] = user
        validated_data['line_item_id'] = line_item_id

        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceFeedback
        fields = '__all__'
