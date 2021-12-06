from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem
from astrobin_apps_equipment.models.equipment_item_group import EquipmentItemKlass


class TelescopeType:
    REFRACTOR_ACHROMATIC = 'REFRACTOR_ACHROMATIC'
    REFRACTOR_SEMI_APOCHROMATIC = 'REFRACTOR_SEMI_APOCHROMATIC'
    REFRACTOR_APOCHROMATIC = 'REFRACTOR_APOCHROMATIC'
    REFRACTOR_NON_ACHROMATIC_GALILEAN = 'REFRACTOR_NON_ACHROMATIC_GALILEAN'
    REFRACTOR_NON_ACHROMATIC_KEPLERIAN = 'REFRACTOR_NON_ACHROMATIC_KEPLERIAN'
    REFRACTOR_SUPERACHROMAT = 'REFRACTOR_SUPERACHROMAT'

    REFLECTOR_DALL_KIRKHAM = 'REFLECTOR_DALL_KIRKHAM'
    REFLECTOR_NASMYTH = 'REFLECTOR_NASMYTH'
    REFLECTOR_RITCHEY_CHRETIEN = 'REFLECTOR_RITCHEY_CHRETIEN'
    REFLECTOR_GREGORIAN = 'REFLECTOR_GREGORIAN'
    REFLECTOR_HERSCHELLIAN = 'REFLECTOR_HERSCHELLIAN'
    REFLECTOR_NEWTONIAN = 'REFLECTOR_NEWTONIAN'

    CATADIOPTRIC_ARGUNOV_CASSEGRAIN = 'CATADIOPTRIC_ARGUNOV_CASSEGRAIN'
    CATADIOPTRIC_KLEVTSOV_CASSEGRAIN = 'CATADIOPTRIC_KLEVTSOV_CASSEGRAIN'
    CATADIOPTRIC_LURIE_HOUGHTON = 'CATADIOPTRIC_LURIE_HOUGHTON'
    CATADIOPTRIC_MAKSUTOV = 'CATADIOPTRIC_MAKSUTOV'
    CATADIOPTRIC_MAKSUTOV_CASSEGRAIN = 'CATADIOPTRIC_MAKSUTOV_CASSEGRAIN'
    CATADIOPTRIC_MODIFIED_DALL_KIRKHAM = 'CATADIOPTRIC_MODIFIED_DALL_KIRKHAM'
    CATADIOPTRIC_SCHMIDT_CAMERA = 'CATADIOPTRIC_SCHMIDT_CAMERA'
    CATADIOPTRIC_SCHMIDT_CASSEGRAIN = 'CATADIOPTRIC_SCHMIDT_CASSEGRAIN'
    CATADIOPTRIC_ACF_SCHMIDT_CASSEGRAIN = 'CATADIOPTRIC_ACF_SCHMIDT_CASSEGRAIN'
    CATADIOPTRIC_ROWE_ACKERMAN_SCHMIDT = 'CATADIOPTRIC_ROWE_ACKERMAN_SCHMIDT'

    CAMERA_LENS = 'CAMERA_LENS'
    BINOCULARS = 'BINOCULARS'


class TelescopeBaseModel(EquipmentItem):
    TELESCOPE_TYPES = (
        (TelescopeType.REFRACTOR_ACHROMATIC, _("Refractor: achromatic")),
        (TelescopeType.REFRACTOR_SEMI_APOCHROMATIC, _("Refractor: semi-apochromatic")),
        (TelescopeType.REFRACTOR_APOCHROMATIC, _("Refractor: apochromatic")),
        (TelescopeType.REFRACTOR_NON_ACHROMATIC_GALILEAN, _("Refractor: non-achromatic Galilean")),
        (TelescopeType.REFRACTOR_NON_ACHROMATIC_KEPLERIAN, _("Refractor: non-achromatic Keplerian")),
        (TelescopeType.REFRACTOR_SUPERACHROMAT, _("Refractor: superachromat")),

        (TelescopeType.REFLECTOR_DALL_KIRKHAM, _("Reflector: Dall-Kirkham")),
        (TelescopeType.REFLECTOR_NASMYTH, _("Reflector: Nasmyth")),
        (TelescopeType.REFLECTOR_RITCHEY_CHRETIEN, _("Reflector: Ritchey Chretien")),
        (TelescopeType.REFLECTOR_GREGORIAN, _("Reflector: Gregorian")),
        (TelescopeType.REFLECTOR_HERSCHELLIAN, _("Reflector: Herschellian")),
        (TelescopeType.REFLECTOR_NEWTONIAN, _("Reflector: Newtonian")),

        (TelescopeType.CATADIOPTRIC_ARGUNOV_CASSEGRAIN, _("Catadioptric: Argunov-Cassegrain")),
        (TelescopeType.CATADIOPTRIC_KLEVTSOV_CASSEGRAIN, _("Catadioptric: Klevtsov-Cassegrain")),
        (TelescopeType.CATADIOPTRIC_LURIE_HOUGHTON, _("Catadioptric: Lurie-Houghton")),
        (TelescopeType.CATADIOPTRIC_MAKSUTOV, _("Catadioptric: Maksutov")),
        (TelescopeType.CATADIOPTRIC_MAKSUTOV_CASSEGRAIN, _("Catadioptric: Maksutov-Cassegrain")),
        (TelescopeType.CATADIOPTRIC_MODIFIED_DALL_KIRKHAM, _("Catadioptric: modified Dall-Kirkham")),
        (TelescopeType.CATADIOPTRIC_SCHMIDT_CAMERA, _("Catadioptric: Schmidt camera")),
        (TelescopeType.CATADIOPTRIC_SCHMIDT_CASSEGRAIN, _("Catadioptric: Schmidt-Cassegrain")),
        (TelescopeType.CATADIOPTRIC_ACF_SCHMIDT_CASSEGRAIN, _("Catadioptric: ACF Schmidt-Cassegrain")),
        (TelescopeType.CATADIOPTRIC_ROWE_ACKERMAN_SCHMIDT, _("Catadioptric: Rowe-Atkinson Schmidt astrograph")),
        (TelescopeType.CAMERA_LENS, _("Camera lens")),
        (TelescopeType.BINOCULARS, _("Binoculars"))
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        max_length=64,
        choices=TELESCOPE_TYPES,
    )

    aperture = models.DecimalField(
        verbose_name=_("Aperture (mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    min_focal_length = models.DecimalField(
        verbose_name=_("Min. focal length (mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    max_focal_length = models.DecimalField(
        verbose_name=_("Max. focal length (mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    weight = models.DecimalField(
        verbose_name=_("Weight (kg)"),
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=2
    )

    def save(self, keep_deleted=False, **kwargs):
        self.klass = EquipmentItemKlass.TELESCOPE
        super().save(keep_deleted, **kwargs)

    class Meta(EquipmentItem.Meta):
        abstract = True
