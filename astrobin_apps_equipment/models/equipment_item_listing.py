# -*- coding: utf-8 -*-


from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import CASCADE, SET_NULL
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer


class EquipmentItemListing(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='created_equipment_item_listings',
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

    name = models.CharField(
        max_length=256,
        null=False,
        blank=False,
    )

    name_de = models.CharField(
        max_length=256,
        null=True,
        blank=True,
    )

    retailer = models.ForeignKey(
        EquipmentRetailer,
        on_delete=CASCADE,
        null=False
    )

    url = models.URLField(
        max_length=512,
    )

    url_de = models.URLField(
        null=True,
        blank=True,
        max_length=512,
    )

    sku = models.CharField(
        max_length=32,
        null=True,
        blank=True,
    )

    item_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    item_object_id = models.PositiveIntegerField()
    item_content_object = GenericForeignKey('item_content_type', 'item_object_id')

    def __str__(self):
        return "%s by %s" % (self.name, self.retailer)

    class Meta:
        unique_together = (
            'name',
            'retailer',
        )
