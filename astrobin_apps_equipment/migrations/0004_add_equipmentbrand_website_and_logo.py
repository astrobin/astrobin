# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-23 09:37
from __future__ import unicode_literals

from django.db import migrations, models

import astrobin_apps_equipment.models.equipment_brand


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin_apps_equipment', '0003_equipmentitemlisting_name_de'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentbrand',
            name='logo',
            field=models.ImageField(blank=True, null=True,
                                    upload_to=astrobin_apps_equipment.models.equipment_brand.logo_upload_path),
        ),
        migrations.AddField(
            model_name='equipmentbrand',
            name='website',
            field=models.URLField(unique=True, blank=True, null=True),
        ),
    ]