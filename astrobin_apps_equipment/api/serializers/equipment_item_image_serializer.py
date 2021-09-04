from rest_framework import serializers


class EquipmentItemImageSerializer(serializers.Serializer):
    class Meta:
        fields = ['image']
        abstract = True
