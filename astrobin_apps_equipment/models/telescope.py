from astrobin_apps_equipment.models.telescope_base_model import TelescopeBaseModel


class Telescope(TelescopeBaseModel):
    class Meta(TelescopeBaseModel.Meta):
        abstract = False
