# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL
from safedelete.models import SafeDeleteModel

from common.upload_paths import upload_path


def logo_upload_path(instance, filename):
    return upload_path('equipment_retailer_logos', instance.created_by.pk if instance.created_by else 0, filename)


class EquipmentRetailer(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='created_equipment_retailers',
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
        max_length=128,
        null=False,
        blank=False,
        unique=True,
    )

    website = models.URLField(
        unique=True,
    )

    logo = models.ImageField(
        upload_to=logo_upload_path,
        null=True,
        blank=True,
    )

    # CSV list of country codes where this retailer operates.
    countries = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )

    def __unicode__(self):
        return self.name
