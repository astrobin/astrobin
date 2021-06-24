from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.models import EquipmentBrand


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrand
        fields = '__all__'

    def create(self, validated_data):
        user = self.context['request'].user

        if not user.groups.filter(name='equipment_moderators').exists():
            raise ValidationError('You don\'t have permission to create a brand')

        validated_data['created_by'] = user
        return super(BrandSerializer, self).create(validated_data)
