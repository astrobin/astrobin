from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL, PROTECT
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models import EquipmentBrand
from astrobin_apps_equipment.services.equipment_item_service import EquipmentItemService
from common.upload_paths import upload_path


def image_upload_path(instance, filename):
    return upload_path('equipment_item_images', instance.created_by.pk if instance.created_by else 0, filename)


class EquipmentItemKlass:
    SENSOR = "SENSOR"
    CAMERA = "CAMERA"
    TELESCOPE = "TELESCOPE"
    MOUNT = "MOUNT"
    FILTER = "FILTER"
    ACCESSORY = "ACCESSORY"
    SOFTWARE = "SOFTWARE"

class EquipmentItem(SafeDeleteModel):
    klass = models.CharField(
        max_length=16,
        null=True,
        blank=False,
        choices=(
            (EquipmentItemKlass.SENSOR, _("Sensor")),
            (EquipmentItemKlass.CAMERA, _("Camera")),
            (EquipmentItemKlass.TELESCOPE, _("Telescope")),
            (EquipmentItemKlass.MOUNT, _("Mount")),
            (EquipmentItemKlass.FILTER, _("Filter")),
            (EquipmentItemKlass.ACCESSORY, _("Accessory")),
            (EquipmentItemKlass.SOFTWARE, _("Software")),
        )
    )
    created_by = models.ForeignKey(
        User,
        related_name='%(app_label)s_%(class)ss_created',
        on_delete=SET_NULL,
        null=True,
        editable=False,
    )

    reviewed_by = models.ForeignKey(
        User,
        related_name='%(app_label)s_%(class)ss_reviewed',
        on_delete=SET_NULL,
        null=True,
        editable=False,
    )

    reviewed_timestamp = models.DateTimeField(
        auto_now=False,
        null=True,
        editable=False,
    )

    reviewer_decision = models.CharField(
        max_length=8,
        choices=[
            ('APPROVED', _('Approved')),
            ('REJECTED', _('Rejected')),
        ],
        null=True,
        editable=False,
    )

    reviewer_rejection_reason = models.CharField(
        max_length=32,
        choices=[
            ('TYPO', 'There\'s a typo in the name of the item'),
            ('WRONG_BRAND', 'The item was assigned to the wrong brand'),
            ('INACCURATE_DATA', 'Some data is inaccurate'),
            ('INSUFFICIENT_DATA', 'Some important data is missing'),
            ('OTHER', _('Other'))
        ],
        null=True,
        editable=False,
    )

    reviewer_comment = models.TextField(
        null=True,
        editable=False,
    )

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

    brand = models.ForeignKey(
        EquipmentBrand,
        related_name='%(app_label)s_brand_%(class)ss',
        on_delete=PROTECT,
        null=False,
    )

    name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
    )

    image = models.ImageField(
        upload_to=image_upload_path,
        null=True,
        blank=True,
    )

    @property
    def item_type(self):
        return EquipmentItemService(self).get_type()

    @property
    def slug(self):
        return slugify(f'{self.brand.name} {self.name}').replace('_', '-')

    def __unicode__(self):
        return '%s %s' % (self.brand.name, self.name)

    class Meta:
        abstract = True
        ordering = [
            'brand__name',
            'name'
        ]
        unique_together = [
            'brand',
            'name'
        ]
