from rest_framework import serializers


class EquipmentItemImageSerializer(serializers.ModelSerializer):
    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.create_thumbnail()
        return instance

    class Meta:
        fields = ['image']
        abstract = True
