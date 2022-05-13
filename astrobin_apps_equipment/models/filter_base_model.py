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


class FilterSize:
    ROUND_1_25_IN = 'ROUND_1_25_IN'
    ROUND_2_IN = 'ROUND_2_IN'
    ROUND_27_MM = 'ROUND_27_MM'
    ROUND_31_MM = 'ROUND_31_MM'
    ROUND_36_MM = 'ROUND_36_MM'
    ROUND_42_MM = 'ROUND_42_MM'
    ROUND_46_MM = 'ROUND_46_MM'
    ROUND_50_MM = 'ROUND_50_MM'
    ROUND_52_MM = 'ROUND_52_MM'
    ROUND_62_MM = 'ROUND_62_MM'
    ROUND_65_MM = 'ROUND_65_MM'
    ROUND_67_MM = 'ROUND_67_MM'
    ROUND_72_MM = 'ROUND_72_MM'
    ROUND_77_MM = 'ROUND_77_MM'
    ROUND_82_MM = 'ROUND_82_MM'
    SQUARE_50_MM = 'SQUARE_50_MM'
    SQUARE_65_MM = 'SQUARE_65_MM'
    SQUARE_100_MM = 'SQUARE_100_MM'
    RECT_101_143_MM = 'RECT_101_143_MM'
    EOS_APS_C = 'EOS_APS_C'
    EOS_FULL = 'EOS_FULL'
    EOS_M = 'EOS_M'
    EOS_R = 'EOS_R'
    SONY = 'SONY'
    SONY_FULL = 'SONY_FULL'
    NIKON = 'NIKON'
    NIKON_Z = 'NIKON_Z'
    NIKON_FULL = 'NIKON_FULL'
    PENTAX = 'PENTAX'
    T_THREAD_CELL_M42 = 'T_THREAD_CELL_M42'
    M_52 = 'M52'
    SCT = 'SCT'
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

    FILTER_SIZES = (
        (FilterSize.ROUND_1_25_IN, _('Round') + ' 1.25"'),
        (FilterSize.ROUND_2_IN, _('Round') + ' 2"'),
        (FilterSize.ROUND_27_MM, _('Round') + ' 27 mm'),
        (FilterSize.ROUND_31_MM, _('Round') + ' 31 mm'),
        (FilterSize.ROUND_36_MM, _('Round') + ' 36 mm"'),
        (FilterSize.ROUND_42_MM, _('Round') + ' 42 mm"'),
        (FilterSize.ROUND_46_MM, _('Round') + ' 46 mm"'),
        (FilterSize.ROUND_50_MM, _('Round') + ' 50 mm"'),
        (FilterSize.ROUND_52_MM, _('Round') + ' 52 mm"'),
        (FilterSize.ROUND_62_MM, _('Round') + ' 62 mm"'),
        (FilterSize.ROUND_65_MM, _('Round') + ' 65 mm"'),
        (FilterSize.ROUND_67_MM, _('Round') + ' 67 mm"'),
        (FilterSize.ROUND_72_MM, _('Round') + ' 72 mm"'),
        (FilterSize.ROUND_77_MM, _('Round') + ' 77 mm"'),
        (FilterSize.ROUND_82_MM, _('Round') + ' 82 mm"'),
        (FilterSize.SQUARE_50_MM, _('Square') + ' 50x50 mm'),
        (FilterSize.SQUARE_65_MM, _('Square') + ' 65x65 mm'),
        (FilterSize.SQUARE_100_MM, _('Square') + ' 100x100 mm'),
        (FilterSize.RECT_101_143_MM, _('Rectangular') + ' 101x143 mm'),
        (FilterSize.EOS_APS_C, 'EOS APS-C'),
        (FilterSize.EOS_FULL, 'EOS Full'),
        (FilterSize.EOS_M, 'EOS M'),
        (FilterSize.EOS_R, 'EOS R'),
        (FilterSize.SONY, 'Sony'),
        (FilterSize.SONY_FULL, 'Sony Full'),
        (FilterSize.NIKON, 'Nikon'),
        (FilterSize.NIKON_Z, 'Nikon Z'),
        (FilterSize.NIKON_FULL, 'Nikon Full'),
        (FilterSize.PENTAX, 'Pentax'),
        (FilterSize.T_THREAD_CELL_M42, 'T-thread cell (M42 x 0.75)'),
        (FilterSize.M_52, 'M52'),
        (FilterSize.SCT, 'SCT'),
        (FilterSize.OTHER, _('Other')),
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        blank=False,
        max_length=16,
        choices=FILTER_TYPES,
    )

    bandwidth = models.DecimalField(
        verbose_name=_("Bandwidth (nm)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )

    size = models.CharField(
        verbose_name=_('Size'),
        null=True,
        blank=True,
        max_length=32,
        choices=FILTER_SIZES,
    )

    other_size = models.DecimalField(
        verbose_name=_('Size (mm)'),
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
    )

    def type_label(self) -> str:
        if self.type is not None:
            for i in self.FILTER_TYPES:
                if self.type == i[0]:
                    return i[1]

        return _("Unknown")

    def size_label(self) -> str:
        if self.size is not None:
            for i in self.FILTER_SIZES:
                if self.size == i[0]:
                    return i[1]

        if self.other_size:
            return f'{self.other_size} mm'

        return _("Unknown")

    def properties(self):
        properties = []

        for item_property in ('type', 'bandwidth', 'size'):
            property_label = self._meta.get_field(item_property).verbose_name
            if item_property == 'type':
                property_value = self.type_label()
            elif item_property == 'size':
                property_value = self.size_label()
            else:
                property_value = getattr(self, item_property)

            if property_value is not None:
                if property_value is not None:
                    if property_value.__class__.__name__ == 'Decimal':
                        property_value = '%g' % property_value
                properties.append({'label': property_label, 'value': property_value})

        return properties

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.FILTER
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
