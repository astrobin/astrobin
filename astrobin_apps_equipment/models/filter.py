from astrobin_apps_equipment.models.filter_base_model import FilterBaseModel


class Filter(FilterBaseModel):
    class Meta(FilterBaseModel.Meta):
        abstract = False
