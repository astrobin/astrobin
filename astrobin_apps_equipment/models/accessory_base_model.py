from astrobin_apps_equipment.models import EquipmentItem


class AccessoryBaseModel(EquipmentItem):
    class Meta(EquipmentItem.Meta):
        abstract = True
