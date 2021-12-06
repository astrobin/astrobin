from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class AccessoryBaseModel(EquipmentItem):
    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.ACCESSORY
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
