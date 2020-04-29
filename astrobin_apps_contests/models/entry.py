# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from safedelete.models import SafeDeleteModel

from astrobin.models import Image
from astrobin_apps_contests.models import Contest
from common.utils import upload_path


def image_upload_path(instance, filename):
    return upload_path('contest-images', instance.user.pk, filename)


class Entry(SafeDeleteModel):
    contest = models.ForeignKey(Contest)

    image = models.ForeignKey(Image)

    image_file = models.ImageField(
        width_field='image_width',
        height_field='image_height',
        upload_to=image_upload_path
    )

    image_width = models.PositiveSmallIntegerField(
        null=False
    )

    image_height = models.PositiveSmallIntegerField(
        null=False
    )

    submitted = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        app_label = 'astrobin_apps_contests'
        ordering = ('-submitted',)
