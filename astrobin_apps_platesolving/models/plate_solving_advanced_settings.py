from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from common.upload_paths import upload_path
from common.validators import FileValidator


def sample_frame_upload_path(instance, filename):
    model = instance.solution.content_object._meta.model_name
    user = instance.solution.content_object.user \
        if model == 'image' \
        else instance.solution.content_object.image.user
    return upload_path('sample_frames', user.pk, filename)


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
        verbose_name=_("Sample raw frame (max 100 MB)"),
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

    show_ecliptic = models.BooleanField(
        default=True,
        verbose_name=_("Show ecliptic"),
    )

    show_galactic_equator = models.BooleanField(
        default=True,
        verbose_name=_("Show galactic equator"),
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

    show_hd = models.BooleanField(
        default=True,
        verbose_name=_("Show HD stars"),
        help_text=_(
            "This catalog uses data from the All-sky Compiled Catalogue of 2.5 million stars (Kharchenko+ 2009), "
            "VizieR catalog: I/280B."
        )
    )

    hd_max_magnitude = models.DecimalField(
        null=True,
        blank=True,
        default=9,
        max_digits=4,
        decimal_places=2,
        verbose_name=_("Max. magnitude"),
        help_text=_(
            "Only HD stars up to this magnitude will be rendered. If left empty, the catalog's default value will be "
            "used."
        ),
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

    show_lbn = models.BooleanField(
        default=True,
        verbose_name=_("Show objects from the Lynds' Catalogue of Bright Nebulae (LBN) (Lynds 1965)"),
    )

    show_ldn = models.BooleanField(
        default=True,
        verbose_name=_("Show objects from the Lynds' Catalogue of Dark Nebulae (LDN) (Lynds 1962)"),
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

    gcvs_max_magnitude = models.DecimalField(
        null=True,
        blank=True,
        max_digits=4,
        decimal_places=2,
        verbose_name=_("Max. magnitude"),
        help_text=_(
            "Only GCVS stars up to this magnitude will be rendered. If left empty, the catalog's default value will be "
            "used."
        ),
    )

    show_tycho_2 = models.BooleanField(
        default=False,
        verbose_name=_("Show Tycho-2 catalog"),
        help_text=mark_safe(
            '<a href="https://wikipedia.org/wiki/Tycho-2_Catalogue" target="_blank">https://wikipedia.org/wiki/Tycho-2_Catalogue</a>'),
    )

    tycho_2_max_magnitude = models.DecimalField(
        null=True,
        blank=True,
        max_digits=4,
        decimal_places=2,
        verbose_name=_("Max. magnitude"),
        help_text=_(
            "Only Tycho-2 stars up to this magnitude will be rendered. If left empty, the catalog's default value will "
            "be used."
        ),
    )

    show_cgpn = models.BooleanField(
        default=True,
        verbose_name=_("Show CGPN objects"),
        help_text=mark_safe(
            '<a href="https://ui.adsabs.harvard.edu/abs/2001A%26A...378..843K/abstract">Catalogue of Galactic Planetary Nebulae</a>'),
    )

    show_quasars = models.BooleanField(
        default=False,
        verbose_name=_("Show quasars"),
        help_text=mark_safe(
            '<a href="https://heasarc.gsfc.nasa.gov/W3Browse/all/milliquas.html">MILLIQUAS - Million Quasars Catalog</a>'),
    )
