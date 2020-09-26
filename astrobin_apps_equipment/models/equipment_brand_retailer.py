# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from safedelete.models import SafeDeleteModel


class EquipmentBrandRetailer(SafeDeleteModel):
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
        max_length=128,
        null=False,
        blank=False
    )

    website = models.URLField()

    logo = models.ImageField(
        upload_to='equipment_brand_retailer_logos',
        null=True,
        blank=True,
    )

    # CSV list of country codes where this retailer operates.
    countries = models.CharField(
        max_length=120,
        null=False,
        blank=False,
    )

    def __unicode__(self):
        return self.name
