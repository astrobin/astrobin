# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-10-05 17:39


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_equipment', '0002_add_url_de'),
    ]

    operations = [
        migrations.AddField(
            model_name='equipmentitemlisting',
            name='name_de',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
