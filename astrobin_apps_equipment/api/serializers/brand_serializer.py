from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_users.services import UserService
from common.constants import GroupName


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrand
        fields = '__all__'
        read_only_fields = ['logo']

    def create(self, validated_data):
        user = self.context['request'].user

        if not UserService(user).is_in_group([GroupName.EQUIPMENT_MODERATORS, GroupName.OWN_EQUIPMENT_MIGRATORS]):
            raise PermissionDenied('You don\'t have permission to create a brand')

        validated_data['created_by'] = user
        return super(BrandSerializer, self).create(validated_data)
