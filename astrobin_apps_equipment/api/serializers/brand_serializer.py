from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from astrobin_apps_equipment.models import EquipmentBrand


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrand
        fields = '__all__'
        read_only_fields = ['logo']

    def create(self, validated_data):
        user = self.context['request'].user

        if not user.groups.filter(name__in=['equipment_moderators', 'own_equipment_migrators']).exists():
            raise PermissionDenied('You don\'t have permission to create a brand')

        validated_data['created_by'] = user
        return super(BrandSerializer, self).create(validated_data)
