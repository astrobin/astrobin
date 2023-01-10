from django.db import models
from django.db.models import PROTECT
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem, Sensor
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class CameraType:
    DEDICATED_DEEP_SKY = 'DEDICATED_DEEP_SKY'
    DSLR_MIRRORLESS = 'DSLR_MIRRORLESS'
    GUIDER_PLANETARY = 'GUIDER_PLANETARY'
    VIDEO = 'VIDEO'
    FILM = 'FILM'
    OTHER = 'OTHER'

class CameraBaseModel(EquipmentItem):
    CAMERA_TYPES = (
        (CameraType.DEDICATED_DEEP_SKY, _('Dedicated deep-sky camera')),
        (CameraType.DSLR_MIRRORLESS, _('General purpose DSLR or mirrorless camera')),
        (CameraType.GUIDER_PLANETARY, _('Guider/Planetary camera')),
        (CameraType.VIDEO, _('General purpose video camera')),
        (CameraType.FILM, _('Film camera')),
        (CameraType.OTHER, _('Other')),
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        max_length=64,
        choices=CAMERA_TYPES,
    )

    sensor = models.ForeignKey(
        Sensor,
        on_delete=PROTECT,
        related_name='%(app_label)s_sensor_%(class)ss',
        null=True,
        blank=True,
        verbose_name=_('Sensor'),
    )

    cooled = models.BooleanField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Cooled'),
    )

    max_cooling = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Max. cooling (C)'),

    )

    back_focus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Back focus (mm)'),
    )

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.CAMERA
        super().save(keep_deleted, **kwargs)

    def type_label(self):
        if self.type is not None:
            for i in self.CAMERA_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    def properties(self):
        properties = []

        for item_property in ('type', 'sensor', 'cooled', 'max_cooling', 'back_focus'):
            property_label = self._meta.get_field(item_property).verbose_name
            if item_property == 'type':
                property_value = self.type_label()
            else:
                property_value = getattr(self, item_property)

            if property_value is not None:
                if property_value is not None:
                    if property_value.__class__.__name__ == 'Decimal':
                        property_value = '%g' % property_value
                    elif property_value.__class__.__name__ == 'bool':
                        property_value = _("Yes") if property_value else _("No")
                properties.append({'label': property_label, 'value': property_value})

        if self.sensor:
            properties += self.sensor.properties()

        return properties

    class Meta(EquipmentItem.Meta):
        abstract = True
        unique_together = [
            'brand',
            'name',
            'cooled',
        ]
