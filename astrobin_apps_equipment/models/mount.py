from astrobin_apps_equipment.models.mount_base_model import MountBaseModel


class Mount(MountBaseModel):
    class Meta(MountBaseModel.Meta):
        abstract = False
