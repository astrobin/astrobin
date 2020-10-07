# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE, SET_NULL
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
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

    url = models.URLField()

    url_de = models.URLField(
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return "%s by %s" % (self.name, self.retailer)

    class Meta:
        unique_together = (
            'name',
            'retailer',
        )
