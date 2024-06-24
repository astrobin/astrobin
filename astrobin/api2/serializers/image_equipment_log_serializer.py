from rest_framework import serializers

from astrobin.models import ImageEquipmentLog


class ImageEquipmentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImageEquipmentLog
        fields = (
            'id',
            'image',
            'equipment_item_content_type',
            'equipment_item_object_id',
            'date',
            'verb',
        )
