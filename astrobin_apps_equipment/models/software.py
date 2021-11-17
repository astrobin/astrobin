from astrobin_apps_equipment.models.software_base_model import SoftwareBaseModel


class Software(SoftwareBaseModel):
    class Meta(SoftwareBaseModel.Meta):
        abstract = False
