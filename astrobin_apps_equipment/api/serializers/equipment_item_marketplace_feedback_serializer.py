from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceFeedback


class EquipmentItemMarketplaceFeedbackSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

    class Meta:
        model = EquipmentItemMarketplaceFeedback
        fields = '__all__'
        depth = 1
