from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models import Accessory, Camera, Filter, Mount, Software, Telescope
from common.upload_paths import upload_path


def image_upload_path(instance, filename):
    return upload_path('equipment_preset_images', instance.user.pk if instance.user else 0, filename)


class EquipmentPreset(SafeDeleteModel):
    created = models.DateTimeField(
        auto_now_add=True,
        null=False,
        editable=False
    )

    updated = models.DateTimeField(
        auto_now=True,
        null=False,
        editable=False
    )

    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='equipment_presets',
    )

    remote_source = models.CharField(
        verbose_name=_('Remote data source'),
        max_length=10,
        null=True,
        blank=True,
    )

    name = models.CharField(
        verbose_name=_('Name'),
        max_length=128,
        null=False,
        blank=False,
    )

    imaging_telescopes = models.ManyToManyField(
        Telescope,
        blank=True,
        related_name='presets_using_for_imaging',
        verbose_name=_("Imaging telescopes or lenses")
    )

    guiding_telescopes = models.ManyToManyField(
        Telescope,
        blank=True,
        related_name='presets_using_for_guiding',
        verbose_name=_("Guiding telescopes or lenses")
    )

    mounts = models.ManyToManyField(
        Mount,
        blank=True,
        related_name='presets_using',
        verbose_name=_("Mounts")
    )

    imaging_cameras = models.ManyToManyField(
        Camera,
        blank=True,
        related_name='presets_using_for_imaging',
        verbose_name=_("Imaging cameras")
    )

    guiding_cameras = models.ManyToManyField(
        Camera,
        blank=True,
        related_name='presets_using_for_guiding',
        verbose_name=_("Guiding cameras")
    )

    software = models.ManyToManyField(
        Software,
        blank=True,
        related_name='presets_using',
        verbose_name=_("Software")
    )

    filters = models.ManyToManyField(
        Filter,
        blank=True,
        related_name='presets_using',
        verbose_name=_("Filters")
    )

    accessories = models.ManyToManyField(
        Accessory,
        blank=True,
        related_name='presets_using',
        verbose_name=_("Accessories")
    )

    description = models.TextField(
        null=True,
        blank=True,
    )

    image_file = models.ImageField(
        upload_to=image_upload_path,
        null=True,
        blank=True,
    )

    # The following fields will be computed asynchronously.

    image_count = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    total_integration = models.FloatField(
        null=True,
        blank=True,
    )

    def __str__(self):
        if self.user:
            return f'{self.name}, by {self.user.userprofile.get_display_name()}'

        if self.remote_source:
            return f'{self.name}, at {self.remote_source}'

        return self.name

    class Meta:
        ordering = ('name',)
        unique_together = ('name', 'user',)
