# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models import CASCADE, SET_NULL
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_retailer import EquipmentRetailer


class EquipmentBrandListing(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='created_equipment_brand_listings',
        on_delete=SET_NULL,
        null=True
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
        on_delete=CASCADE,
        null=False
    )

    retailer = models.ForeignKey(
        EquipmentRetailer,
        on_delete=CASCADE,
        null=False
    )

    url = models.URLField()

    def __unicode__(self):
        return "%s by %s" % (self.brand, self.retailer)
