# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from safedelete.models import SafeDeleteModel

from astrobin_apps_contests.models import Entry


class Vote(SafeDeleteModel):
    user = models.ForeignKey(User)

    entry = models.ForeignKey(Entry)

    score = models.PositiveSmallIntegerField(
        null=False
    )

    submitted = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        app_label = 'astrobin_apps_contests'
        ordering = ('-submitted',)
        unique_together = ('user', 'entry')
