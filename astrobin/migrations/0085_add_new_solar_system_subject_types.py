# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2020-12-01 08:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0084_migrate_STAR_TRALS_typo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='solar_system_main_subject',
            field=models.CharField(
                blank=True,
                choices=[
                    (b'SUN', 'Sun'),
                    (b'MOON', "Earth's Moon"),
                    (b'MERCURY', 'Mercury'),
                    (b'VENUS', 'Venus'),
                    (b'MARS', 'Mars'),
                    (b'JUPITER', 'Jupiter'),
                    (b'SATURN', 'Saturn'),
                    (b'URANUS', 'Uranus'),
                    (b'NEPTUNE', 'Neptune'),
                    (b'MINOR_PLANET', 'Minor planet'),
                    (b'COMET', 'Comet'),
                    (b'OCCULTATION', 'Occultation'),
                    (b'CONJUNCTION', 'Conjunction'),
                    (b'PARTIAL_LUNAR_ECLIPSE', 'Partial lunar eclipse'),
                    (b'TOTAL_LUNAR_ECLIPSE', 'Total lunar eclipse'),
                    (b'PARTIAL_SOLAR_ECLIPSE', 'Partial solar eclipse'),
                    (b'ANULAR_SOLAR_ECLIPSE', 'Anular solar eclipse'),
                    (b'TOTAL_SOLAR_ECLIPSE', 'Total solar eclipse'),
                    (b'OTHER', 'Other')],
                help_text='If the main subject of your image is a body in the solar system, please select which (or which type) it is.',
                max_length=32,
                null=True,
                verbose_name='Main solar system subject'),
        ),
        migrations.AlterField(
            model_name='image',
            name='subject_type',
            field=models.CharField(
                choices=[
                    (None, b'---------'),
                    (b'DEEP_SKY', 'Deep sky object or field'),
                    (b'SOLAR_SYSTEM', 'Solar system body or event'),
                    (b'WIDE_FIELD', 'Extremely wide field'),
                    (b'STAR_TRAILS', 'Star trails'),
                    (b'NORTHERN_LIGHTS', 'Northern lights'),
                    (b'GEAR', 'Gear'),
                    (b'OTHER', 'Other')
                ],
                max_length=16,
                verbose_name='Subject type'),
        ),
    ]
