# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2020-02-13 07:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_platesolving', '0004_pixinsight_coordinate_matrix'),
    ]

    operations = [
        migrations.AddField(
            model_name='solution',
            name='pixinsight_svg_annotation_620',
            field=models.ImageField(blank=True, null=True, upload_to=b'pixinsight-solutions-620'),
        ),
    ]
