# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-07-07 10:43
from __future__ import unicode_literals

import common.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0107_remove_userprofile_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='app',
            name='registrar',
            field=models.ForeignKey(editable=False, on_delete=models.SET(common.utils.get_sentinel_user), related_name='app_api_key', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='gear',
            name='master',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='astrobin.Gear'),
        ),
    ]