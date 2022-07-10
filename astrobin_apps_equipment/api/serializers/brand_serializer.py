from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from astrobin_apps_equipment.models import EquipmentBrand
from common.constants import GroupName


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrand
        fields = '__all__'
        read_only_fields = ['logo']

    def create(self, validated_data):
        user = self.context['request'].user

        if not user.groups.filter(
                name__in=[GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]
        ).exists():
            raise PermissionDenied('You don\'t have permission to create a brand')

        validated_data['created_by'] = user
        return super(BrandSerializer, self).create(validated_data)
