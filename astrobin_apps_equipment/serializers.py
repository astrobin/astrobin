from rest_framework import serializers

from astrobin_apps_equipment.models import Brand, EquipmentItem


class BrandSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Brand
        fields = '__all__'


class EquipmentItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EquipmentItem
        fields = '__all__'
