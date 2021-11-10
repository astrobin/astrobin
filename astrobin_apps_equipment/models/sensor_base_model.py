from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem


class SensorBaseModel(EquipmentItem):
    quantum_efficiency = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    pixel_size = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    pixel_width = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    pixel_height = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    sensor_width = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    sensor_height = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
    )

    full_well_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    read_noise = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2,
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
    )

    color_or_mono = models.CharField(
        max_length=2,
        null=True,
        blank=True,
        choices=(
            ('M', _('Monochromatic')),
            ('C', _('Color')),
            ('MC', _('Monochromatic/Color'))
        )
    )

    specification_url = models.URLField(
        blank=True,
        null=True,
    )

    class Meta(EquipmentItem.Meta):
        abstract = True
