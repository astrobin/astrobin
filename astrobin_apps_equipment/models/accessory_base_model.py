from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class AccessoryType:
    COMPUTER = 'COMPUTER'
    DEW_MITIGATION = 'DEW_MITIGATION'
    FIELD_DEROTATOR = 'FIELD_DEROTATOR'
    FILTER_WHEEL = 'FILTER_WHEEL'
    FLAT_BOX = 'FLAT_BOX'
    FOCAL_MODIFIER_FIELD_CORRECTOR = 'FOCAL_MODIFIER_FIELD_CORRECTOR'
    FOCUSER = 'FOCUSER'
    OAG = 'OAG'
    OBSERVATORY_CONTROL = 'OBSERVATORY_CONTROL'
    OBSERVATORY_DOME = 'OBSERVATORY_DOME'
    POWER_DISTRIBUTION = 'POWER_DISTRIBUTION'
    WEATHER_MONITORING = 'WEATHER_MONITORING'
    MOUNT_CONTROL = 'MOUNT_CONTROL'
    OTHER = 'OTHER'


class AccessoryBaseModel(EquipmentItem):
    ACCESSORY_TYPES = (
        (AccessoryType.COMPUTER, _('Computer')),
        (AccessoryType.DEW_MITIGATION, _('Dew mitigation')),
        (AccessoryType.FIELD_DEROTATOR, _('Field derotator / camera rotator')),
        (AccessoryType.FILTER_WHEEL, _('Filter wheel')),
        (AccessoryType.FLAT_BOX, _('Flat box')),
        (AccessoryType.FOCAL_MODIFIER_FIELD_CORRECTOR, _('Focal modifier / field corrector')),
        (AccessoryType.FOCUSER, _('Focuser')),
        (AccessoryType.OAG, _('Off-axis guider')),
        (AccessoryType.OBSERVATORY_CONTROL, _('Observatory control')),
        (AccessoryType.OBSERVATORY_DOME, _('Observatory dome')),
        (AccessoryType.POWER_DISTRIBUTION, _('Power distribution')),
        (AccessoryType.WEATHER_MONITORING, _('Weather monitoring')),
        (AccessoryType.MOUNT_CONTROL, _('Mount control')),
        (AccessoryType.OTHER, _('Other')),
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        blank=False,
        max_length=32,
        choices=ACCESSORY_TYPES,
    )

    def type_label(self) -> str:
        if self.type is not None:
            for i in self.ACCESSORY_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    def properties(self):
        return [
            {
                'label': _('Type'),
                'value': self.type_label()
            }
        ]

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.ACCESSORY
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
