from rest_framework import serializers

from astrobin_apps_equipment.models import EquipmentItemGroup


class EquipmentItemGroupSerializer(serializers.ModelSerializer):
    sensor_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    camera_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    telescope_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    mount_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    filter_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    accessory_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    software_set = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = EquipmentItemGroup
        fields = '__all__'
