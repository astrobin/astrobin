from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PlateSolvingSettings(models.Model):
    blind = models.BooleanField(
        default=True,
        verbose_name=_("Perform a blind solve"),
        help_text=_("Attempt to solve with no hints. In most cases this will work, but it will take longer."),
    )

    scale_units = models.CharField(
        null=True,
        blank=True,
        max_length=16,
        choices=(
            ('degwidth', _("Width of the field in degrees")),
            ('arcminwidth', _("Width of the field in arcminutes")),
            ('arcsecperpix', _("Resolution of the field in arcseconds/pixel")),
        ),
        verbose_name=_("Field size units"),
        help_text=("The units for the min/max field size settings below."),
    )

    scale_min = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=3,
        verbose_name=_("Min field size"),
        help_text=_("Estimate the lower bound for the width of this field."),
    )

    scale_max = models.DecimalField(
        null=True,
        blank=True,
        max_digits=8,
        decimal_places=3,
        verbose_name=_("Max field size"),
        help_text=_("Estimate the upper bound for the width of this field."),
    )

    center_ra = models.DecimalField(
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        verbose_name=_("Center RA"),
        help_text=_("Center RA of the field in degrees, 0.000 to 360.000"),
    )

    center_dec = models.DecimalField(
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name=_("Center dec"),
        help_text=_("Center dec of the field in degrees, -90.000 to +90.000"),
    )

    radius = models.DecimalField(
        null=True,
        blank=True,
        max_digits=7,
        decimal_places=3,
        validators=[MinValueValidator(0), MaxValueValidator(360)],
        verbose_name=_("Radius"),
        help_text=_(
            "Tells the plate-solving engine to look within these many degrees of the given center RA and dec position."),
    )

    downsample_factor = models.DecimalField(
        null=True,
        blank=True,
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1.01), MaxValueValidator(99.99)],
        verbose_name=_("Downsample factor"),
        help_text=_(
            "Downsample (bin) your image by this factor before performing source detection. This often helps with "
            "saturated images, noisy images, and large images. 2 and 4 are commonly-useful values."
        )
    )

    use_sextractor = models.BooleanField(
        default=False,
        verbose_name=_("Use SExtractor"),
        help_text=_(
            "Use the SourceExtractor program to detect stars, not Nova's built-in program."
        )
    )
