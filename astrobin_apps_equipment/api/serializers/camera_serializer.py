from django.db.models import Q
from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.services.camera_service import CameraService


class CameraSerializer(EquipmentItemSerializer):
    modified = serializers.BooleanField(required=False, default=False)
    variants = serializers.SerializerMethodField()

    def get_variants(self, camera):
        if camera.modified or (camera.type == CameraType.DSLR_MIRRORLESS and camera.cooled):
            return []

        variants = Camera.objects.filter(
            ~Q(pk=camera.pk) &
            Q(brand=camera.brand) &
            Q(name=camera.name) &
            CameraService.variant_inclusion_query()
        )

        return CameraSerializer(variants, many=True).data

    class Meta(EquipmentItemSerializer.Meta):
        model = Camera
        fields = '__all__'
        abstract = False
