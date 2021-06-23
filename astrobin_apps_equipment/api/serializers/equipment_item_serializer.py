from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class EquipmentItemSerializer(serializers.Serializer):
    class Meta:
        fields = [
            'created_by',
            'created',
            'updated',
            'brand',
            'name',
            'image',
        ]
        abstract = True

    def create(self, validated_data):
        user = self.context['request'].user

        if not user.groups.filter(name='equipment_moderators').exists():
            raise ValidationError('You don\'t have permission to create an equipmen item')

        validated_data['created_by'] = user
        return super(EquipmentItemSerializer, self).create(validated_data)
