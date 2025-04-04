from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel


class MeasurementPreset(SafeDeleteModel):
    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False
    )

    modified = models.DateTimeField(
        auto_now=True,
        null=False,
        editable=False
    )

    user = models.ForeignKey(
        User,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='measurement_presets',
    )

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=100,
        null=False,
        blank=False,
    )

    notes = models.TextField(
        verbose_name=_('Notes'),
        null=True,
        blank=True,
    )

    width_arcseconds = models.FloatField(
        verbose_name=_("Width (arcseconds)"),
        default=3600.0,  # Default to 1 degree (3600 arcseconds)
    )

    height_arcseconds = models.FloatField(
        verbose_name=_("Height (arcseconds)"),
        default=3600.0,  # Default to 1 degree (3600 arcseconds)
    )

    def __str__(self):
        return f'{self.name}, by {self.user.userprofile.get_display_name()}'

    class Meta:
        ordering = ('name',)
        unique_together = ('name', 'user',)
        verbose_name = _('Measurement Preset')
        verbose_name_plural = _('Measurement Presets')
