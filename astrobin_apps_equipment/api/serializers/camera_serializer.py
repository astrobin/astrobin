from annoying.functions import get_object_or_None
from django.db.models import Q
from rest_framework import serializers

from astrobin_apps_equipment.api.serializers.equipment_item_serializer import EquipmentItemSerializer
from astrobin_apps_equipment.models import Camera
from astrobin_apps_equipment.models.camera_base_model import CameraType
from astrobin_apps_equipment.services.camera_service import CameraService


class CameraSerializerWithoutVariants(EquipmentItemSerializer):
    modified = serializers.BooleanField(required=False, default=False)

    class Meta(EquipmentItemSerializer.Meta):
        model = Camera
        fields = '__all__'
        abstract = False


class CameraSerializer(CameraSerializerWithoutVariants):
    variants = serializers.SerializerMethodField()
    parent_variant = serializers.SerializerMethodField()

    def get_variants(self, camera):
        if camera.modified or (camera.type == CameraType.DSLR_MIRRORLESS and camera.cooled):
            return []

        variants = Camera.objects.filter(
            ~Q(pk=camera.pk) &
            Q(brand=camera.brand) &
            Q(name=camera.name) &
            CameraService.variant_inclusion_query()
        ).order_by('-modified', '-cooled')

        return CameraSerializerWithoutVariants(variants, many=True).data

    def get_parent_variant(self, camera):
        if not camera.modified and (camera.type == CameraType.DSLR_MIRRORLESS and not camera.cooled):
            return None

        parent_variant = get_object_or_None(Camera,
            ~Q(pk=camera.pk) &
            Q(brand=camera.brand) &
            Q(name=camera.name) &
            CameraService.variant_exclusion_query()
        )

        return CameraSerializerWithoutVariants(parent_variant).data

    class Meta(CameraSerializerWithoutVariants.Meta):
        pass
