from django.db import models
from django.db.models import PROTECT
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem, Sensor


class CameraBaseModel(EquipmentItem):
    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        max_length=64,
        choices=(
            ('DEDICATED_DEEP_SKY', _('Dedicated deep-sky camera')),
            ('DSLR_MIRRORLESS', _('General purpose DSLR or mirrorless camera')),
            ('GUIDER_PLANETARY', _('Guider/Planetary camera')),
            ('VIDEO', _('General purpose video camera')),
            ('FILM', _('Film camera')),
            ('OTHER', _('Other')),
        ),
    )

    sensor = models.ForeignKey(
        Sensor,
        on_delete=PROTECT,
        related_name='%(app_label)s_sensor_%(class)ss',
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

    class Meta(EquipmentItem.Meta):
        abstract = True
