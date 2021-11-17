from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item import EquipmentItemKlass


class SoftwareBaseModel(EquipmentItem):
    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.SOFTWARE
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
