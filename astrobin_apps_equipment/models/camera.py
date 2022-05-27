from django.db import models
from django.utils.translation import gettext_lazy

from astrobin_apps_equipment.models.camera_base_model import CameraBaseModel, CameraType


class Camera(CameraBaseModel):
    # The `modified` property is here instead of in `CameraBaseModel` because it cannot be edited via an edit proposal.
    modified = models.BooleanField(
        default=False,
        editable=False,
    )

    def __str__(self):
        base = super().__str__()

        if self.type == CameraType.DSLR_MIRRORLESS:
            modified = gettext_lazy('modified')
            cooled = gettext_lazy('cooled')

            if self.modified and self.cooled:
                return f'{base} ({modified} + {cooled})'
            elif self.modified:
                return f'{base} ({modified})'
            elif self.cooled:
                return f'{base} ({cooled})'

        return base

    class Meta(CameraBaseModel.Meta):
        abstract = False
        ordering = CameraBaseModel.Meta.ordering + ['modified']
        unique_together = [
            'brand',
            'name',
            'modified',
            'cooled',
        ]
