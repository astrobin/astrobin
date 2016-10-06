# Django
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import ugettext as _
# This app
from astrobin_apps_platesolving.solver import Solver


class PlateSolvingSettings(models.Model):
    blind = models.BooleanField(
        default = True,
        null = False,
        verbose_name = _("Perform a blind solve"),
        help_text = _("Attempt to solve with no hints. In most cases this will work, but it will take longer."),
    )

    scale_units = models.CharField(
        null = True,
        blank = True,
        max_length = 16,
        choices = (
            ('degwidth', _("Width of the field in degrees")),
            ('arcminwidth', _("Width of the field in arcminutes")),
            ('arcsecperpix', _("Resolution of the field in arcseconds/pixel")),
        ),
        verbose_name = _("Field size units"),
        help_text = ("The units for the min/max field size settings below."),
    )

    scale_min = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 8,
        decimal_places = 3,
        verbose_name = _("Min field size"),
        help_text = _("Estimate the lower bound for the width of this field."),
    )

    scale_max = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 8,
        decimal_places = 3,
        verbose_name = _("Max field size"),
        help_text = _("Estimate the upper bound for the width of this field."),
    )

    center_ra = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 7,
        decimal_places = 3,
        validators = [MinValueValidator(0), MaxValueValidator(360)],
        verbose_name = _("Center RA"),
        help_text = _("Center RA of the field in degrees, 0.000 to 360.000"),
    )

    center_dec = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 7,
        decimal_places = 3,
        validators = [MinValueValidator(-90), MaxValueValidator(90)],
        verbose_name = _("Center dec"),
        help_text = _("Center dec of the field in degrees, -90.000 to +90.000"),
    )

    radius = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 7,
        decimal_places = 3,
        validators = [MinValueValidator(0), MaxValueValidator(360)],
        verbose_name = _("Radius"),
        help_text = _("Tells the plate-solving engine to look within these many degrees of the given center RA and dec position."),
    )


class Solution(models.Model):
    STATUS_CHOICES = (
        (Solver.MISSING, 'Missing'),
        (Solver.PENDING, 'Pending'),
        (Solver.FAILED,  'Failed'),
        (Solver.SUCCESS, 'Success'),
    )

    settings = models.OneToOneField(
        PlateSolvingSettings,
        related_name = 'solution',
        null = True)

    status = models.PositiveIntegerField(
        default = 0,
        choices = STATUS_CHOICES,
    )

    submission_id = models.PositiveIntegerField(
        null = True,
        blank = True,
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.TextField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    image_file = models.ImageField(
        upload_to = 'solutions',
        null = True,
        blank = True,
    )

    skyplot_zoom1 = models.ImageField(
        upload_to = 'skyplots',
        null = True,
        blank = True,
    )

    objects_in_field = models.CharField(
        max_length = 1024,
        null = True,
        blank = True,
    )

    ra = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    dec = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    pixscale = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    orientation = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )

    radius = models.DecimalField(
        null = True,
        blank = True,
        max_digits = 6,
        decimal_places = 3,
    )


    def __unicode__(self):
        return "solution_%d" % self.id

    def clear(self):
        self.status = Solver.MISSING
        self.submission_id = None
        self.image_file.delete()
        self.image_file = None
        self.skyplot_zoom1.delete()
        self.skyplot_zoom1 = None
        self.objects_in_field = None
        self.ra = None
        self.dec = None
        self.pixscale = None
        self.orientation = None
        self.radius = None
        self.save()

    class Meta:
        app_label = 'astrobin_apps_platesolving'
        verbose_name = "Solution"
        unique_together = ('content_type', 'object_id',)
