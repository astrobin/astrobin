from astrobin_apps_equipment.models.sensor_base_model import SensorBaseModel


class Sensor(SensorBaseModel):
    class Meta(SensorBaseModel.Meta):
        abstract = False
