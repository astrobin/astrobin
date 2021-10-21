from rest_framework import serializers


class EquipmentItemImageSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ['image']
        abstract = True
