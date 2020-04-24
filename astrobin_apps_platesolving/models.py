from django.conf import settings
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from astrobin_apps_platesolving.solver import Solver
from common.utils import upload_path
from common.validators import FileValidator


def sample_frame_upload_path(instance, filename):
    model = instance.solution.content_object._meta.model_name
    user = instance.solution.content_object.user \
        if model == u'image' \
        else instance.solution.content_object.image.user
    return upload_path('sample_frames', user.pk, filename)


class PlateSolvingSettings(models.Model):
    blind = models.BooleanField(
        default=True,
        null=False,
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


class PlateSolvingAdvancedSettings(models.Model):
    FONT_SIZE_CHOICES = (
        ("S", _("Small")),
        ("M", _("Medium")),
        ("L", _("Large")),
    )

    sample_raw_frame_file = models.FileField(
        upload_to=sample_frame_upload_path,
        validators=(FileValidator(allowed_extensions=(settings.ALLOWED_FITS_IMAGE_EXTENSIONS)),),
        max_length=256,
        null=True,
        blank=True,
        verbose_name=_("Sample raw frame (max 200 MB)"),
        help_text=_(
            "To improve the accuracy of your plate-solution even further, please upload one of the XISF or " +
            "FITS files from your data set. Such files normally have date and time headers that will allow AstroBin " +
            "to calculate solar system body ephemerides and find planets and asteroids in your image (provided you " +
            "also add location information to it).<br/><br/>For maximum accuracy, it's recommended that you use " +
            "PixInsight's native and open format XISF. Learn more about XISF here:<br/><br/><a " +
            "href=\"https://pixinsight.com/xisf/\" target=\"_blank\">https://pixinsight.com/xisf/</a><br/><br/> " +
            "<strong>Please note:</strong> it's very important that the XISF or FITS file you upload is aligned to " +
            "your processed image, otherwise the object annotations will not match. To improve your chances at a " +
            "successful accurate plate-solution, calibrate your file the usual way (dark/bias/flats) but do not " +
            "stretch it.")
    )

    scaled_font_size = models.CharField(
        default="M",
        choices=FONT_SIZE_CHOICES,
        max_length=1,
        verbose_name=_("Scaled font size"),
        help_text=_("Font size of the annotations on your main image page")
    )

    show_grid = models.BooleanField(
        default=True,
        verbose_name=_("Show equatorial grid"),
    )

    show_constellation_borders = models.BooleanField(
        default=True,
        verbose_name=_("Show constellation borders"),
    )

    show_constellation_lines = models.BooleanField(
        default=True,
        verbose_name=_("Show constellation lines"),
    )

    show_named_stars = models.BooleanField(
        default=True,
        verbose_name=_("Show named stars"),
    )

    show_messier = models.BooleanField(
        default=True,
        verbose_name=_("Show Messier objects"),
    )

    show_ngc_ic = models.BooleanField(
        default=True,
        verbose_name=_("Show NGC and IC objects"),
    )

    show_vdb = models.BooleanField(
        default=True,
        verbose_name=_("Show VdB objects"),
    )

    show_sharpless = models.BooleanField(
        default=True,
        verbose_name=_("Show Sharpless objects"),
    )

    show_barnard = models.BooleanField(
        default=True,
        verbose_name=_("Show Barnard objects"),
    )

    show_pgc = models.BooleanField(
        default=False,
        verbose_name=_("Show PGC objects"),
    )

    show_planets = models.BooleanField(
        default=True,
        verbose_name=_("Show planets"),
        help_text=_("Only available if your image at least an acquisition time and an accurate location"),
    )

    show_asteroids = models.BooleanField(
        default=True,
        verbose_name=_("Show asteroids"),
        help_text=_("Only available if your image at least an acquisition time and an accurate location"),
    )

    show_gcvs = models.BooleanField(
        default=False,
        verbose_name=_("Show GCVS stars"),
        help_text=_("General Catalog of Variable Stars"),
    )

    show_tycho_2 = models.BooleanField(
        default=False,
        verbose_name=_("Show Tycho-2 catalog"),
        help_text=mark_safe(
            '<a href="https://wikipedia.org/wiki/Tycho-2_Catalogue" target="_blank">https://wikipedia.org/wiki/Tycho-2_Catalogue</a>'),
    )

    show_cgpn = models.BooleanField(
        default=True,
        verbose_name=_("Show CGPN objects"),
        help_text=mark_safe(
            '<a href="https://ui.adsabs.harvard.edu/abs/2001A%26A...378..843K/abstract">Catalogue of Galactic Planetary Nebulae</a>'),
    )


class PlateSolvingAdvancedTask(models.Model):
    serial_number = models.CharField(
        max_length=32,
        null=False,
        blank=False,
    )

    created = models.DateTimeField(
        auto_now_add=True
    )

    active = models.BooleanField(
        default=True,
    )

    task_params = models.TextField(
        null=False,
        blank=False,
    )


class Solution(models.Model):
    STATUS_CHOICES = (
        (Solver.MISSING, 'Missing'),
        (Solver.PENDING, 'Pending'),
        (Solver.FAILED, 'Failed'),
        (Solver.SUCCESS, 'Success'),
        (Solver.ADVANCED_PENDING, 'Advanced pending'),
        (Solver.ADVANCED_FAILED, 'Advanced failed'),
        (Solver.ADVANCED_SUCCESS, 'Advanced success'),
    )

    settings = models.OneToOneField(
        PlateSolvingSettings,
        related_name='solution',
        null=True)

    status = models.PositiveIntegerField(
        default=Solver.MISSING,
        choices=STATUS_CHOICES,
    )

    submission_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.TextField()
    content_object = fields.GenericForeignKey('content_type', 'object_id')

    image_file = models.ImageField(
        upload_to='solutions',
        null=True,
        blank=True,
    )

    skyplot_zoom1 = models.ImageField(
        upload_to='images/skyplots',
        null=True,
        blank=True,
    )

    objects_in_field = models.TextField(
        null=True,
        blank=True,
    )

    ra = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    dec = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    pixscale = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    orientation = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    radius = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    annotations = models.TextField(
        null=True,
        blank=True,
    )

    pixinsight_serial_number = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )

    pixinsight_svg_annotation_hd = models.ImageField(
        upload_to='pixinsight-solutions-hd',
        null=True,
        blank=True,
    )

    pixinsight_svg_annotation_regular = models.ImageField(
        upload_to='pixinsight-solutions-regular',
        null=True,
        blank=True,
    )

    advanced_settings = models.OneToOneField(
        PlateSolvingAdvancedSettings,
        related_name='solution',
        null=True,
    )

    advanced_ra = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_ra_top_left = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_ra_top_right = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_ra_bottom_left = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_ra_bottom_right = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_dec = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=9,
    )

    advanced_dec_top_left = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_dec_top_right = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_dec_bottom_left = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=9,
    )

    advanced_dec_bottom_right = models.DecimalField(
        null=True,
        blank=True,
        max_digits=11,
        decimal_places=8,
    )

    advanced_pixscale = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    advanced_orientation = models.DecimalField(
        null=True,
        blank=True,
        max_digits=6,
        decimal_places=3,
    )

    advanced_flipped = models.NullBooleanField()

    advanced_wcs_transformation = models.CharField(
        null=True,
        blank=True,
        max_length=64,
    )

    advanced_matrix_rect = models.CharField(
        null=True,
        blank=True,
        max_length=131,
    )

    advanced_matrix_delta = models.IntegerField(
        null=True,
        blank=True,
    )

    advanced_ra_matrix = models.TextField(
        null=True,
        blank=True,
    )

    advanced_dec_matrix = models.TextField(
        null=True,
        blank=True,
    )

    advanced_annotations = models.TextField(
        null=True,
        blank=True,
    )

    advanced_annotations_regular = models.TextField(
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return "solution_%d" % self.id

    def _do_clear_basic(self):
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
        self.annotations = None

    def _do_clear_advanced(self):
        if self.status > Solver.SUCCESS:
            self.status = Solver.SUCCESS

        self.pixinsight_serial_number = None
        self.pixinsight_svg_annotation_hd.delete()
        self.pixinsight_svg_annotation_hd = None
        self.pixinsight_svg_annotation_regular.delete()
        self.pixinsight_svg_annotation_regular = None

        self.advanced_ra = None
        self.advanced_ra_bottom_left = None
        self.advanced_ra_bottom_right = None
        self.advanced_ra_top_left = None
        self.advanced_ra_top_right = None
        self.advanced_dec = None
        self.advanced_dec_bottom_left = None
        self.advanced_dec_bottom_right = None
        self.advanced_dec_top_left = None
        self.advanced_dec_top_right = None
        self.advanced_pixscale = None
        self.advanced_orientation = None
        self.advanced_radius = None
        self.advanced_ra_matrix = None
        self.advanced_dec_matrix = None
        self.advanced_matrix_rect = None
        self.advanced_matrix_delta = None
        self.advanced_annotations = None
        self.advanced_annotations_regular = None

    def clear(self):
        self._do_clear_basic()
        self._do_clear_advanced()
        self.save()

    def clear_advanced(self):
        self._do_clear_advanced()
        self.save()

    class Meta:
        app_label = 'astrobin_apps_platesolving'
        verbose_name = "Solution"
        unique_together = ('content_type', 'object_id',)
