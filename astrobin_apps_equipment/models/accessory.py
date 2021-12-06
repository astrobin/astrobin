from astrobin_apps_equipment.models.accessory_base_model import AccessoryBaseModel


class Accessory(AccessoryBaseModel):
    class Meta(AccessoryBaseModel.Meta):
        abstract = False
