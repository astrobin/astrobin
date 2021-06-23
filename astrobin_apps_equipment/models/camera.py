from django.db import models
from django.db.models import PROTECT
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem, Sensor


class Camera(EquipmentItem):
    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        max_length=64,
        choices=(
            ('CCD', _('CCD')),
            ('CMOS', _('CMOS')),
            ('DSLR', _('DSLR')),
            ('GUIDER/PLANETARY', _('Guider/Planetary')),
            ('FILM', _('Film')),
            ('COMPACT', _('Compact')),
            ('VIDEO', _('Video camera')),
        ),
    )

    sensor = models.ForeignKey(
        Sensor,
        on_delete=PROTECT,
        related_name='cameras',
        null=True,
        blank=True,
    )

    cooled = models.BooleanField(
        default=False,
    )

    max_cooling = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
    )

    back_focus = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
