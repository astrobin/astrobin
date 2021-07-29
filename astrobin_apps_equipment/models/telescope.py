from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_equipment.models import EquipmentItem


class Telescope(EquipmentItem):
    TELESCOPE_TYPES = (
        ("REFR ACHRO", _("Refractor: achromatic")),
        ("REFR SEMI-APO", _("Refractor: semi-apochromatic")),
        ("REFR APO", _("Refractor: apochromatic")),
        ("REFR NON-ACHRO GALILEAN", _("Refractor: non-achromatic Galilean")),
        ("REFR NON-ACHRO KEPLERIAN", _("Refractor: non-achromatic Keplerian")),
        ("REFR SUPERACHRO", _("Refractor: superachromat")),

        ("REFL DALL-KIRKHAM", _("Reflector: Dall-Kirkham")),
        ("REFL NASMYTH", _("Reflector: Nasmyth")),
        ("REFL RITCHEY CHRETIEN", _("Reflector: Ritchey Chretien")),
        ("REFL GREGORIAN", _("Reflector: Gregorian")),
        ("REFL HERSCHELLIAN", _("Reflector: Herschellian")),
        ("REFL NEWTONIAN", _("Reflector: Newtonian")),

        ("CATA ARGUNOV-CASSEGRAIN", _("Catadioptric: Argunov-Cassegrain")),
        ("CATA KLEVTSOV-CASSEGRAIN", _("Catadioptric: Klevtsov-Cassegrain")),
        ("CATA LURIE-HOUGHTON", _("Catadioptric: Lurie-Houghton")),
        ("CATA MAKSUTOV", _("Catadioptric: Maksutov")),
        ("CATA MAKSUTOV-CASSEGRAIN", _("Catadioptric: Maksutov-Cassegrain")),
        ("CATA MOD DALL-KIRKHAM", _("Catadioptric: modified Dall-Kirkham")),
        ("CATA SCHMIDT CAMERA", _("Catadioptric: Schmidt camera")),
        ("CATA SCHMIDT-CASSEGRAIN", _("Catadioptric: Schmidt-Cassegrain")),
        ("CATA ACF SCHMIDT-CASSEGRAIN", _("Catadioptric: ACF Schmidt-Cassegrain")),
        ("CATA ROWE-ACKERMANN SCHMIDT", _("Catadioptric: Rowe-Atkinson Schmidt astrograph")),
        ("CAMERA LENS", _("Camera lens")),
        ("BINOCULARS", _("Binoculars"))
    )

    type = models.CharField(
        verbose_name=_('Type'),
        null=False,
        max_length=64,
        choices=TELESCOPE_TYPES,
    )

    min_aperture = models.DecimalField(
        verbose_name=_("Min. aperture (mm)"),
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=2,
    )

    max_aperture = models.DecimalField(
        verbose_name=_("Max. aperture (mm)"),
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
