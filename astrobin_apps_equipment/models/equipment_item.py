from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL, PROTECT
from django.utils.translation import ugettext_lazy as _
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
            ('ACCEPTED', _('Accepted')),
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
