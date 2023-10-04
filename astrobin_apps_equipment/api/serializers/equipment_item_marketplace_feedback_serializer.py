from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemMarketplaceFeedback


class EquipmentItemMarketplaceFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentItemMarketplaceFeedback
        fields = '__all__'
        depth = 1
