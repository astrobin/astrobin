# Generated by Django 2.2.24 on 2024-07-30 19:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0211_add_rockchuck_summit_observatory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='image',
            name='subject_type',
            field=models.CharField(
                choices=[(None, '---------'), ('DEEP_SKY', 'Deep sky object or field'),
                         ('SOLAR_SYSTEM', 'Solar system body or event'), ('WIDE_FIELD', 'Extremely wide field'),
                         ('STAR_TRAILS', 'Star trails'), ('NORTHERN_LIGHTS', 'Northern lights'),
                         ('NOCTILUCENT_CLOUDS', 'Noctilucent clouds'), ('LANDSCAPE', 'Landscape'),
                         ('ARTIFICIAL_SATELLITE', 'Artificial satellite'), ('GEAR', 'Gear'), ('OTHER', 'Other')],
                max_length=20, verbose_name='Subject type'
            ),
        ),
    ]