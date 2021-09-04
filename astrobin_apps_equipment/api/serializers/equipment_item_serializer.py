from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied


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
        read_only_fields = ['image']
        abstract = True

    def create(self, validated_data):
        user = self.context['request'].user

        if not user.groups.filter(name='equipment_moderators').exists():
            raise PermissionDenied('You don\'t have permission to create an equipment item')

        validated_data['created_by'] = user
        return super(EquipmentItemSerializer, self).create(validated_data)
