from django.db.models import Q

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
