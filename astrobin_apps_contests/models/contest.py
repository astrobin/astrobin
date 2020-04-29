# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from safedelete.models import SafeDeleteModel


class Contest(SafeDeleteModel):
    user = models.ForeignKey(
        User,
        editable=False
    )

    title = models.CharField(
        max_length=200,
        null=False,
        blank=False,
        unique=True
    )

    description = models.TextField(
        null=False,
        blank=False
    )

    rules = models.TextField(
        null=False,
        blank=False
    )

    prizes = models.TextField(
        null=True
    )

    start_date = models.DateField(
        null=False,
        validators=[MinValueValidator(date.today() + timedelta(days=7))],
    )

    end_date = models.DateField(
        null=False,
        validators=[MinValueValidator(date.today() + timedelta(days=14))],
    )

    min_participants = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(2)],
        null=False
    )

    max_participants = models.PositiveSmallIntegerField(
        null=True,
    )

    created = models.DateTimeField(
        editable=False,
        auto_now_add=True
    )

    updated = models.DateTimeField(
        editable=False,
        auto_now=True,
    )

    class Meta:
        app_label = 'astrobin_apps_contests'
        ordering = ('-created',)
