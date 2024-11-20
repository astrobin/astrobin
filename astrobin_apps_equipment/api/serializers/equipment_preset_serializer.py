from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from astrobin_apps_equipment.models import EquipmentPreset


class EquipmentPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPreset
        fields = '__all__'
        read_only_fields = [
            'id',
            'deleted',
            'created',
            'updated',
            'user',
            'remote_source',
            'image_file',
            'thumbnail',
            'total_integration',
            'image_count',
        ]

    def validate_name(self, value):
        user = self.context['request'].user
        instance = getattr(self, 'instance', None)

        # Check if another preset exists with same name for this user
        exists = self.Meta.model.objects.filter(
            user=user,
            name__iexact=value
        ).exclude(
            pk=instance.pk if instance else None
        ).exists()

        if exists:
            raise ValidationError("You already have a preset with this name.")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
