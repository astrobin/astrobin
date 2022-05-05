from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class FilterType:
    H_ALPHA = 'H_ALPHA'
    H_BETA = 'H_BETA'
    SII = 'SII'
    OIII = 'OIII'
    NII = 'NII'
    UV = 'UV'
    IR = 'IR'
    MULTIBAND = 'MULTIBAND'
    LP = 'LP'
    L = 'L'
    R = 'R'
    G = 'G'
    B = 'B'
    ND = 'ND'
    UHC = 'UHC'
    SKY_GLOW = 'SKY_GLOW'
    SOLAR = 'SOLAR'
    LUNAR = 'LUNAR'
    PLANETARY = 'PLANETARY'
    COMETARY = 'COMETARY'
    PHOTOMETRIC_U = 'PHOTOMETRIC_U'
    PHOTOMETRIC_B = 'PHOTOMETRIC_B'
    PHOTOMETRIC_V = 'PHOTOMETRIC_V'
    PHOTOMETRIC_R = 'PHOTOMETRIC_R'
    PHOTOMETRIC_I = 'PHOTOMETRIC_I'
    OTHER = 'OTHER'


class FilterBaseModel(EquipmentItem):
    FILTER_TYPES = (
        (FilterType.H_ALPHA, _("Hydrogen-alpha (Hα)")),
        (FilterType.H_BETA, _("Hydrogen-beta (Hβ)")),
        (FilterType.SII, _("Sulfur-II (SII)")),
        (FilterType.OIII, _("Oxygen-III (OIII)")),
        (FilterType.NII, _("Nitrogen-II (NII)")),
        (FilterType.UV, _("Ultraviolet (UV)")),
        (FilterType.IR, _("Infrared (IR)")),
        (FilterType.MULTIBAND, _("Multiband")),
        (FilterType.LP, _("Light pollution suppression")),
        (FilterType.L, _("Luminance/clear (L)")),
        (FilterType.R, _("Red channel (R)")),
        (FilterType.G, _("Green channel (G)")),
        (FilterType.B, _("Blue channel (B)")),
        (FilterType.ND, _("Neutral density (ND)")),
        (FilterType.UHC, _("Ultra High Contrast (UHC)")),
        (FilterType.SKY_GLOW, _("Sky glow")),
        (FilterType.SOLAR, _("Solar")),
        (FilterType.LUNAR, _("Lunar")),
        (FilterType.PLANETARY, _("Planetary")),
        (FilterType.COMETARY, _("Cometary")),
        (FilterType.PHOTOMETRIC_U, _("Photometric Ultraviolet")),
        (FilterType.PHOTOMETRIC_B, _("Photometric Blue")),
        (FilterType.PHOTOMETRIC_V, _("Photometric Visual")),
        (FilterType.PHOTOMETRIC_R, _("Photometric Red")),
        (FilterType.PHOTOMETRIC_I, _("Photometric Infrared")),
        (FilterType.OTHER, _("Other")),
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        blank=False,
        max_length=16,
        choices=FILTER_TYPES,
    )

    bandwidth = models.PositiveSmallIntegerField(
        verbose_name=_("Bandwidth (nm)"),
        null=True,
        blank=True,
    )

    size = models.DecimalField(
        verbose_name=_('Size (mm)'),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    def type_label(self):
        if self.type is not None:
            for i in self.FILTER_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    def properties(self):
        properties = []

        for item_property in ('type', 'brandwidth', 'size'):
            property_label = self._meta.get_field(item_property).verbose_name
            if item_property == 'type':
                property_value = self.type_label()
            else:
                property_value = getattr(self, item_property)

            if property_value is not None:
                properties.append({'label': property_label, 'value': property_value})

        return properties

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.FILTER
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
