# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from safedelete.models import SafeDeleteModel


class RemoteSourceAffiliate(SafeDeleteModel):
    code = models.CharField(max_length=8)
    name = models.CharField(max_length=64)
    url = models.CharField(max_length=256)
    affiliation_start = models.DateTimeField(null=True, blank=True)
    affiliation_expiration = models.DateField(null=True, blank=True)
    image_file = models.ImageField(
        upload_to='remote_source_affiliates',
        null=True,
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'astrobin_apps_remote_source_affiliation'
        ordering = ['-created']
