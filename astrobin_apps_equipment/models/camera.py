from astrobin_apps_equipment.models.camera_base_model import CameraBaseModel


class Camera(CameraBaseModel):
    class Meta(CameraBaseModel.Meta):
        abstract = False
