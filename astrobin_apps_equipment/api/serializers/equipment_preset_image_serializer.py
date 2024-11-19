from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentPreset


class EquipmentPresetImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPreset
        fields = ['image_file']
