# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-12-01 08:38


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0085_add_new_solar_system_subject_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='last_seen',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
