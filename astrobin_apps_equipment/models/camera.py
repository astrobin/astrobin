from django.db import models

from astrobin_apps_equipment.models.camera_base_model import CameraBaseModel


class Camera(CameraBaseModel):
    # The `modified` property is here instead of in `CameraBaseModel` because it cannot be edited via an edit proposal.
    modified = models.BooleanField(
        default=False,
        editable=False,
    )

    class Meta(CameraBaseModel.Meta):
        abstract = False
