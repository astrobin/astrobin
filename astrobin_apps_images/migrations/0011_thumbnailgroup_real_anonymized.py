# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-12-28 13:40


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin_apps_images', '0010_add_regular_anonymized_and_regular_crop_anonymized'),
    ]

    operations = [
        migrations.AddField(
            model_name='thumbnailgroup',
            name='real_anonymized',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]

