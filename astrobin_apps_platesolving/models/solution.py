from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import ugettext_lazy as _

from astrobin.tasks import invalidate_cdn_caches
from astrobin_apps_platesolving.models.plate_solving_advanced_settings import PlateSolvingAdvancedSettings
from astrobin_apps_platesolving.models.plate_solving_settings import PlateSolvingSettings
from astrobin_apps_platesolving.solver import Solver


class Solution(models.Model):
    STATUS_CHOICES = (
        (Solver.MISSING, _('Missing')),
        (Solver.PENDING, _('Basic pending')),
        (Solver.FAILED, _('Basic failed')),
        (Solver.SUCCESS, _('Basic success')),
        (Solver.ADVANCED_PENDING, _('Advanced pending')),
        (Solver.ADVANCED_FAILED, _('Advanced failed')),
        (Solver.ADVANCED_SUCCESS, _('Advanced success')),
    )

    created = models.DateTimeField(
        editable=False,
        auto_now_add=True,
    )

    settings = models.OneToOneField(
        PlateSolvingSettings,
        related_name='solution',
        null=True,
        on_delete=models.CASCADE
    )

    status = models.PositiveIntegerField(
        default=Solver.MISSING,
        choices=STATUS_CHOICES,
    )

    submission_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
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

    pixinsight_finding_chart = models.ImageField(
        upload_to='pixinsight-finding-charts',
        null=True,
        blank=True,
    )

    pixinsight_finding_chart_small = models.ImageField(
        upload_to='pixinsight-finding-charts',
        null=True,
        blank=True,
    )

    advanced_settings = models.OneToOneField(
        PlateSolvingAdvancedSettings,
        related_name='solution',
        null=True,
        on_delete=models.CASCADE
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

    def __str__(self):
        return "solution_%d" % self.id

    def save(self, *args, **kwargs):
        super(Solution, self).save(*args, **kwargs)

        # Save target to trigger index update if applicable.
        if (self.status in (
                Solver.SUCCESS,
                Solver.FAILED,
                Solver.ADVANCED_SUCCESS,
                Solver.ADVANCED_FAILED)):
            self.content_object.save(keep_deleted=True)

    def delete(self, *args, **kwargs):
        self._do_clear_basic()
        self._do_clear_advanced()
        super(Solution, self).delete(*args, **kwargs)

    def _do_clear_basic(self):
        self.status = Solver.MISSING
        self.submission_id = None

        invalidate_urls = []

        if self.image_file and self.image_file.url:
            invalidate_urls.append(self.image_file.url)

        self.image_file.delete(save=False)
        self.image_file = None

        if self.skyplot_zoom1 and self.skyplot_zoom1.url:
            invalidate_urls.append(self.skyplot_zoom1.url)

        self.skyplot_zoom1.delete()
        self.skyplot_zoom1 = None

        self.objects_in_field = None
        self.ra = None
        self.dec = None
        self.pixscale = None
        self.orientation = None
        self.radius = None
        self.annotations = None

        if len(invalidate_urls) > 0:
            invalidate_cdn_caches.delay(invalidate_urls)

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
