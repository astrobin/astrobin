from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class SensorBaseModel(EquipmentItem):
    quantum_efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Quantum efficiency'),
    )

    pixel_size = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Pixel size (μm)"),
    )

    pixel_width = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Pixel width"),
    )

    pixel_height = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Pixel height"),
    )

    sensor_width = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Sensor width (mm)"),
    )

    sensor_height = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Sensor height (mm)"),
    )

    full_well_capacity = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
        verbose_name = _("Full well capacity"),
    )

    read_noise = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
        verbose_name=_("Read noise (e-)"),
    )

    frame_rate = models.PositiveSmallIntegerField(
        verbose_name=_("Frame rate"),
        help_text='FPS',
        null=True,
        blank=True,
    )

    adc = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name="ADC",
    )

    color_or_mono = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        choices=(
            ('C', _('Color')),
            ('M', _('Monochromatic')),
        ),
        verbose_name=_("Color or mono")
    )

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.SENSOR
        super().save(keep_deleted, **kwargs)

    def properties(self):
        properties = []

        for item_property in (
            'quantum_efficiency',
            'pixel_size',
            'pixel_width',
            'pixel_height',
            'sensor_width',
            'sensor_height',
            'full_well_capacity',
            'read_noise',
            'frame_rate',
            'adc',
            'color_or_mono',
        ):
            property_label = self._meta.get_field(item_property).verbose_name
            property_value = getattr(self, item_property)

            if property_value is not None:
                if property_value is not None:
                    if property_value.__class__.__name__ == 'Decimal':
                        property_value = '%g' % property_value
                properties.append({'label': property_label, 'value': property_value})

        return properties

    class Meta(EquipmentItem.Meta):
        abstract = True
