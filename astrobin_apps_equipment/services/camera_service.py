from django.db.models import Q
from rest_framework.exceptions import ValidationError

from astrobin_apps_equipment.models.camera_base_model import CameraType


class CameraService:
    @staticmethod
    def variant_inclusion_query() -> Q:
        return Q(
            Q(type=CameraType.DSLR_MIRRORLESS) &
            Q(
                 Q(modified=True) | Q(cooled=True)
            )
        )

    @staticmethod
    def variant_exclusion_query() -> Q:
        return Q(
            Q(
                Q(type=CameraType.DSLR_MIRRORLESS) & ~Q(modified=True) & ~Q(cooled=True)
            ) |
            ~Q(type=CameraType.DSLR_MIRRORLESS)
        )

    @staticmethod
    def validate(attrs):
        variant_of = attrs['variant_of'] if 'variant_of' in attrs else None
        camera_type = attrs['type']

        if camera_type == CameraType.DSLR_MIRRORLESS and variant_of:
            raise ValidationError("DSLR/Mirrorless cameras do not support variants")
