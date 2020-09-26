# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import CASCADE
from safedelete.models import SafeDeleteModel

from astrobin_apps_equipment.models.equipment_brand import EquipmentBrand
from astrobin_apps_equipment.models.equipment_brand_retailer import EquipmentBrandRetailer


class EquipmentBrandListing(SafeDeleteModel):
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
        EquipmentBrandRetailer,
        on_delete=CASCADE,
        null=False
    )

    url = models.URLField()

    def __unicode__(self):
        return "%s by %s" % (self.brand, self.retailer)
