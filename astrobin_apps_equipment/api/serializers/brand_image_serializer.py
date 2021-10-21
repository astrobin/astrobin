from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentBrand


class BrandImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquipmentBrand
        fields = ['logo']
