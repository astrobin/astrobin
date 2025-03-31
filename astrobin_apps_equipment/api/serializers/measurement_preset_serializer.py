from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.models import MeasurementPreset


class MeasurementPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementPreset
        fields = '__all__'
        read_only_fields = [
            'id',
            'deleted',
            'created',
            'modified',
            'user',
        ]

    def validate_name(self, value):
        if not value or value.strip() == '':
            raise ValidationError("Preset name cannot be empty.")
        return value

    def validate_width_arcseconds(self, value):
        if value <= 0:
            raise ValidationError("Width must be a positive number.")
        return value
        
    def validate_height_arcseconds(self, value):
        if value <= 0:
            raise ValidationError("Height must be a positive number.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
