# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL
from safedelete.models import SafeDeleteModel


class EquipmentBrand(SafeDeleteModel):
    created_by = models.ForeignKey(
        User,
        related_name='create_equipment_brands',
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

    name = models.CharField(
        max_length=128,
        null=False,
        blank=False
    )

    def __unicode__(self):
        return self.name
