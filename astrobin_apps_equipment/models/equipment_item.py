from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL, PROTECT
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models import EquipmentBrand
from common.upload_paths import upload_path


def image_upload_path(instance, filename):
    return upload_path('equipment_item_images', instance.created_by.pk if instance.created_by else 0, filename)


class EquipmentItem(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='%(app_label)s_%(class)ss_created',
        on_delete=SET_NULL,
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
        related_name='%(app_label)s_%(class)ss',
        on_delete=PROTECT,
        null=False,
    )

    name = models.CharField(
        max_length=128,
        null=False,
        blank=False,
        unique=True,
    )

    image = models.ImageField(
        upload_to=image_upload_path,
    )

    def __unicode__(self):
        return '%s %s' % (self.brand.name, self.name)

    class Meta:
        abstract = True
        ordering = [
            'brand__name',
            'name'
        ]
