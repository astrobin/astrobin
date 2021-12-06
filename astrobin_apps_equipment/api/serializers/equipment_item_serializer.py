from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from astrobin_apps_equipment.models import EquipmentBrand


class EquipmentItemSerializer(serializers.ModelSerializer):
    # brand = serializers.PrimaryKeyRelatedField(required=False, queryset=EquipmentBrand.objects.all)

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

        if not user.groups.filter(name__in=['equipment_moderators', 'own_equipment_migrators']).exists():
            raise PermissionDenied('You don\'t have permission to create an equipment item')

        validated_data['created_by'] = user
        return super(EquipmentItemSerializer, self).create(validated_data)
