from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.models import EquipmentPreset


class EquipmentPresetSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentPreset
        fields = '__all__'
        read_only_fields = ['id', 'deleted', 'created', 'updated', 'user', 'remote_source',]

    def create(self, validated_data):
        user = self.context['request'].user
        name = validated_data['name']

        if self.Meta.model.objects.filter(user=user, name=name).exists():
            raise ValidationError(f'User {user.username} already has a preset with name {name}.')

        validated_data['user'] = user
        return super().create(validated_data)
