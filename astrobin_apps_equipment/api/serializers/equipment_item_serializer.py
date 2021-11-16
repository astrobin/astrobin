from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied


class EquipmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        fields = [
            'klass',
            'created_by',
            'reviewed_by',
            'reviewed_timestamp',
            'reviewer_decision',
            'reviewer_rejection_reason',
            'reviewer_comment',
            'created',
            'updated',
            'brand',
            'name',
            'website',
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
